# FEDMA Ethical AI-Powered Marketing Charter

FEDMA (the Federation of European Direct and Interactive Marketing) is the
European trade body representing national direct and data-driven marketing
associations; it has a long history of producing sector self-regulatory
codes (its direct marketing and data-protection codes predate GDPR and were
referenced during GDPR's drafting). Its Ethical AI-Powered Marketing Charter
addresses the newer problem the ICC Code covers only at a high level: what
specifically changes when targeting, content generation, and decisioning in
a campaign are done by AI/ML systems rather than human marketers. Zora
treats it as the applied, AI-specific layer on top of the ICC Code's general
floor — the ICC Code asks whether a communication is honest and identifiable;
the FEDMA Charter asks whether the AI system behind it can be explained,
audited, and held accountable for how it got there.

## Principles

- **Transparency** — organizations must be able to explain, in terms
  meaningful to the audience and to regulators, that and how AI is used in a
  marketing communication or decision (targeting, personalization, content
  generation, dynamic pricing), rather than treating the AI system as an
  unexplainable black box.
- **Fairness** — AI-driven targeting, segmentation, and personalization must
  be assessed for disparate or discriminatory impact across protected or
  vulnerable groups, not just for overall performance lift; a model
  optimizing conversion can still be unfair if its gains are concentrated by
  excluding or exploiting specific segments.
- **Accountability** — a named, human-accountable owner must exist for each
  AI-driven marketing system's outcomes; "the model did it" is not an
  acceptable end point for a compliance or ethics review, and organizations
  must be able to audit and correct AI decisions after deployment, not only
  at design time.
- **Privacy** — AI systems that personalize or target using personal data
  must meet data-protection-by-design standards (data minimization, purpose
  limitation, lawful basis) at the point the AI pipeline is built, not
  retrofitted after the fact, and must account for inferred or derived data
  (attributes the AI predicts, not just data directly collected) as personal
  data in its own right.

## How Zora applies this

Zora runs this as a four-lane audit specifically for AI-assisted campaigns,
rating each lane by severity:

- **Blocking** — no human-accountable owner is identified for an AI
  targeting or content system, or the organization cannot explain in plain
  terms what the AI is doing and why (transparency/accountability failure).
  Must be resolved before the board treats the campaign as launchable.
- **Material risk** — fairness testing across protected/vulnerable segments
  has not been done or documented for an AI targeting/personalization
  system, or the AI pipeline uses inferred/derived personal data without
  a clear lawful basis. Flag and require documented mitigation.
- **Advisory** — the system passes the four lanes but relies on a
  third-party AI vendor whose own transparency and fairness documentation is
  thin — noted as a supply-chain risk for the board to weigh, since
  accountability under this Charter does not transfer away just because the
  model is licensed rather than built in-house.
