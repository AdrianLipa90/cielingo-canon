# CIELingo × GREMLIN Genomic Grammar v0.1

Status: experimental computational representation.

This increment connects CIELingo to the complete tool registry advertised by a
GREMLIN MCP runtime without vendoring GREMLIN into CIELingo. The bridge discovers
the surface dynamically, checks a small invariant core, preserves every additional
tool it finds, and keeps CIELingo/NOEMA authority boundaries intact.

The genomic representation is:

```text
KAKU -> RADYKAŁ -> KONCEPT -> ZDANIE -> AKAPIT -> ROZDZIAŁ -> KSIĄŻKA
```

Relations between adjacent units can carry anchor-to-anchor displacement,
edge-to-edge empty spacing, orientation, helical phase and chromatin context.
The distinction is mandatory: helical phase is computed from anchor displacement,
not from the length of the empty gap between motifs.

The representation is intended to test whether relational features improve
prediction beyond sequence-only baselines. It is not evidence that DNA is
literally a linguistic system and it does not replace the genetic code.

## GREMLIN routing intent

For genomic work, the full discovered GREMLIN surface is available to an
orchestrator. Typical read-only roles include relation scanning, contradiction
checks, evidence audit, memory/similarity analysis, decomposition, synthesis and
PhaseNav reference analysis. Species selection is delegated to OCTOPUS from an
auditable semantic payload rather than hard-coded in CIELingo.

Mutation-shaped tools remain fail-closed unless the caller provides explicit
authorization. Successful GREMLIN output cannot grant canon, NOEMA CURRENT,
production-runtime write, or memory-write authority inside CIELingo.
