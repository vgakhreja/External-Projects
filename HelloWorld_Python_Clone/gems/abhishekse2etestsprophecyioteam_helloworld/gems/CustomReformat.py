from prophecy.cb.server.base.ComponentBuilderBase import *
from pyspark.sql import *
from pyspark.sql.functions import *
import dataclasses
import re

from prophecy.cb.ui.UISpecUtil import getColumnsToHighlight, computeTargetName, SchemaFields, getColumnsInSchema, \
    validateExpTable, ColumnsUsage, getTargetTokens, sanitizedColumn
from prophecy.cb.util.CSVUtils import parse_escaped_csv, unparse_escaped_csv, CSVParseException
from prophecy.cb.ui.uispec import *
from prophecy.cb.util.StringUtils import isBlank
from prophecy.cb.server.base import WorkflowContext

class CustomReformat(ComponentSpec):
    name: str = "CustomReformat"
    category: str = "Transform"
    gemDescription: str = "Edits column names or values using expressions."
    docUrl: str = "https://docs.prophecy.io/low-code-spark/gems/transform/reformat/"



    def optimizeCode(self) -> bool:
        return True

    @dataclass(frozen=True)
    class CustomReformatProperties(ComponentProperties):
        columnsSelector: List[str] = field(default_factory=list)
        expressions: List[SColumnExpression] = field(default_factory=list)
        activeTab: str = "expressions"
        importLanguage: str = "${$.workflow.metainfo.frontEndLanguage}"
        importString: str = ""

    def onClickFunc(self, portId: str, column: str, state: Component[CustomReformatProperties]):
        existingTargetNames = list(map(lambda exp: exp.target, state.properties.expressions))
        targetTokens = getTargetTokens(column, [exp.split('.') for exp in existingTargetNames], True)
        targetCol = '.'.join(targetTokens)
        expressions = state.properties.expressions
        expressions.append(SColumnExpression(targetCol, SColumn.getSColumn(sanitizedColumn(column)), ""))
        return state.bindProperties(dataclasses.replace(state.properties, expressions=expressions))

    def allColumnsSelectionFunc(self, portId: str, state: Component[CustomReformatProperties]):
        columnsInSchema = getColumnsInSchema(portId, state, SchemaFields.TopLevel)
        expressions = list(
            map(lambda column: SColumnExpression.getSColumnExpression(sanitizedColumn(column)), columnsInSchema))
        state.properties.expressions.extend(expressions)
        return state.bindProperties(dataclasses.replace(state.properties, expressions=state.properties.expressions))

    def expressions_to_csv(self, state: Component[CustomReformatProperties]) -> Component[CustomReformatProperties]:
        exprCSV = []
        for e in state.properties.expressions:
            linepart = [e.target, e.expression.rawExpression]
            if len(e.description):
                linepart.append(e.description)
            exprCSV.append(linepart)
        csv_string = unparse_escaped_csv(exprCSV)
        return state.bindProperties(dataclasses.replace(state.properties, importString=csv_string))

    def csv_to_expressions(self, state: Component[CustomReformatProperties]) -> Component[CustomReformatProperties]:
        exprs = []
        # for (target, exp, desc) in parse_escaped_csv(state.properties.importString):
        for line in parse_escaped_csv(state.properties.importString, field_min=2, field_max=2):
            (target, exp) = line
            exprs.append(SColumnExpression(
                target.strip(),
                SColumn(
                    exp,
                    state.properties.importLanguage,
                    col(exp),
                    [exp]
                ),
                ""
            ))
        return state.bindProperties(dataclasses.replace(state.properties, expressions=exprs))

    def dialog(self) -> Dialog:
        expTable = ExpTable("CustomReformat Expression") \
            .enableVirtualization() \
            .bindProperty("expressions") \
            .withCopilotEnabledExpressions().allowCopilotExpressionsFix()
        bulkEdit = StackLayout(height="100%") \
            .addElement(
            NativeText("Edit the CustomReformat expressions in the field below. Use the format of \"name,expr\".")
        ).addElement(
            NativeText("Use ``...`` to wrap multi-line expressions.")
        ).addElement(
            Editor(height="100%", language="${component.properties.importLanguage}") \
                .bindProperty("importString")
        )
        refTabs = Tabs() \
            .bindProperty("activeTab") \
            .addTabPane(
            TabPane("Expressions", "expressions").addElement(expTable)
        ).addTabPane(
            TabPane("Advanced", "advanced").addElement(bulkEdit)
        )
        return Dialog("CustomReformat").addElement(
            ColumnsLayout(gap="1rem", height="100%")
                .addColumn(
                Ports(
                    allowInputRename=True,
                    selectedFieldsProperty="columnsSelector",
                    singleColumnClickCallback=self.onClickFunc,
                    allColumnsSelectionCallback=self.allColumnsSelectionFunc
                ),
                "content"
            )
                .addColumn(refTabs, "5fr")
        ).withCopilotEnabledAutoSuggestionProperties()

    def validate(self, context: WorkflowContext, component: Component[CustomReformatProperties]) -> List[Diagnostic]:
        diagnostics = []
        expTableDiags = validateExpTable(component.properties.expressions, "expressions", component,
                                         ColumnsUsage.WithoutInputAlias)
        expTableDiags = [e.setDiagnosticFix(CopilotDiagnosticFix("expression")) for e in expTableDiags]
        diagnostics.extend(expTableDiags)

        if component.properties.activeTab == "advanced":
            try:
                parse_escaped_csv(component.properties.importString, field_min=2, field_max=3)
            except CSVParseException as e:
                diagnostics.append(Diagnostic(f"properties.importString", str(e), SeverityLevelEnum.Error))

        return diagnostics

    def onChange(self, context: WorkflowContext, oldState: Component[CustomReformatProperties], newState: Component[CustomReformatProperties]) -> Component[
        CustomReformatProperties]:

        oldProps = oldState.properties
        newProps = newState.properties

        if oldProps.activeTab == "advanced" and newProps.activeTab == "expressions":
            try:
                newState = self.csv_to_expressions(newState)
                newProps = newState.properties

            except CSVParseException:
                pass
        elif oldProps.activeTab == "expressions" and newProps.activeTab == "advanced":
            newState = self.expressions_to_csv(newState)
            newProps = newState.properties

        expressions = newProps.expressions

        usedColExps = getColumnsToHighlight(expressions, newState)

        return newState.bindProperties(dataclasses.replace(newProps,
                                               columnsSelector=usedColExps,
                                               expressions=list(
                                                   map(lambda exp: exp.withRowId(), expressions))))

    def getCPStmt(self, component: Component[CustomReformatProperties]) -> Optional[SelectStmt]:
        return SelectStmt(
            component.component,
            [ProjectionExpression(expression.target, expression.expression.rawExpression) for expression in
             component.properties.expressions]
        )

    class CustomReformatCode(ComponentCode):
        def __init__(self, newProps):
            self.props: CustomReformat.CustomReformatProperties = newProps

        def apply(self, spark: SparkSession, in0: DataFrame) -> DataFrame:
            if len(self.props.expressions) > 0:
                selectColumns = map(lambda x: x.column(), self.props.expressions)
                return in0.select(*selectColumns)
            else:
                return in0
