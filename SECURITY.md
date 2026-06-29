# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in DOE Helper, please **do not** open a public GitHub issue. Instead, please report it responsibly via email.

### How to Report

**Email**: martinjgallagher@icloud.com

Include in your report:
- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Any suggested mitigation

**What to expect:**
- Acknowledgment of receipt within 48 hours
- Updates on progress toward a fix every 7 days
- Notification when a patch is released (typically within 30 days)
- Credit in the release notes (if you wish)

## Vulnerability Disclosure Timeline

1. **Report received**: Acknowledged within 48 hours
2. **Investigation**: Up to 2 weeks to investigate and develop a fix
3. **Patch**: Release via a new version on PyPI
4. **Disclosure**: Security advisory published after patch release
5. **Credit**: Contributor credited in CHANGELOG and release notes (optional)

## Supported Versions

Security updates are provided for:

| Version | Status | Support Until |
|---------|--------|----------------|
| 0.3.x   | Current | End of life (TBD) |
| 0.2.x   | Unmaintained | N/A |
| < 0.2   | Unsupported | N/A |

We recommend always using the latest version.

## Security Best Practices

### For Users

1. **Keep DOE Helper updated**: Run `pip install --upgrade doehelper` regularly
2. **Review dependencies**: DOE Helper's dependencies are minimal and well-maintained
3. **Validate external data**: If accepting experiment configs from untrusted sources, validate them first
4. **Protect result files**: Results and intermediate files may contain sensitive experimental data

### For Contributors

1. **Use security scanners**: We run `pip-audit` and Bandit in CI
2. **Avoid hardcoded secrets**: Never commit API keys, credentials, or sensitive data
3. **Validate user input**: All CLI arguments and JSON configs are validated
4. **Report responsibly**: Follow the disclosure timeline above

## Known Limitations

- DOE Helper uses `eval()`-style constraint parsing with an AST allowlist. Constraint expressions are validated but should only come from trusted sources.
- Temporary files written to the system temp directory may be readable by other users on multi-user systems.

## Dependencies Security

We use automated scanning to detect vulnerable dependencies:

- **pip-audit** runs in CI to check for known vulnerabilities
- **Dependabot** can be enabled for automated dependency updates
- Critical dependencies are pinned to specific versions

See [pyproject.toml](pyproject.toml) for the complete dependency list.

## Security Contact

**Email**: martinjgallagher@icloud.com

## Changes to This Policy

We may update this policy. Changes will be posted here with a note about when the policy was last updated.

---

Last updated: June 29, 2026
