# Governance and maintenance

`4alvit` is the primary maintainer and owns repository access, release approval,
security triage and technical decisions. Contributors propose issues and pull
requests, document compatibility impact and provide tests. Automated CI and
review bots assist review; they are not backup maintainers or independent release
owners. Public decisions are recorded in issues, pull requests and release notes.
Maintainer changes follow the same documented contribution and test policy.

Anyone may contribute under [CONTRIBUTING.md](CONTRIBUTING.md) and the MIT license.
Use a public issue for a technical disagreement and explain the evidence and
tradeoffs. Conduct reports follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
No formal voting body, paid support promise or external governance foundation is
claimed. The maintainer prioritizes reproducible correctness and security defects,
compatibility, then roadmap work.

## Continuity limitation

As confirmed by the maintainer on 2026-10-13, there is **no backup person or tested
mechanism** that can restore maintenance and repository/CI/release access within
one week of the maintainer becoming unavailable. Public source can be forked,
but a fork does not restore signing keys, protected environments or publishing
rights. OpenSSF `access_continuity` and `bus_factor` remain unmet.

The next governance improvement is to recruit an authorized backup, document
least-privilege access and recovery, and test recovery without publishing secrets.
No such arrangement is represented as already implemented.
