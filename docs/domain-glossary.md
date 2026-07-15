# Domain glossary

- **Argument**: a role plus a normalized, grounded half-open token span.
- **Event frame**: a given trigger and its extracted arguments within one document.
- **Document loss**: `1 - argument micro-F1`; structural failure has loss 1.
- **Confidence**: a higher-is-better aggregate of generated-token transition log probabilities.
- **Whole-document acceptance**: accept only if every frame is valid and the minimum frame score
  meets the threshold.
- **Certification labels**: sealed outcomes opened once to select/certify a policy.
- **Final labels**: sealed outcomes unavailable until the certificate artifact is locked.
- **Shift labels**: outcomes used only after in-domain artifacts are immutable.
- **Infeasible**: no candidate meets all formal risk, acceptance, and sample preconditions.
- **Analysis ID**: immutable identifier derived from all bound code, data, system and configuration
  artifacts.

