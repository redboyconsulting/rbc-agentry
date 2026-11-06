# Declarative Workflows

A _Declarative Workflow_ is defined as a single YAML file and
may be executed locally no different from any regular `Workflow` that is defined by code.

The difference is that the workflow definition is loaded from a YAML file instead of being defined in code:

```c#
Workflow workflow = DeclarativeWorkflowBuilder.Build("Marketing.yaml", options);
```

These legacy examples target the .NET workflow
[samples in the upstream repository](https://github.com/microsoft/agent-framework/tree/main/dotnet/samples/03-workflows/Declarative).
The .NET implementation is not included in this Python-only repository.

For Python declarative workflows, see the
[Python samples](../../python/samples/03-workflows/declarative).
