# Source and license notices

The reference implementation was copied from the user's Spotlightning workspace. Its exact files and hashes are listed in [source provenance](docs/source-provenance.json). The source repository had no root license file at handoff time; TestReceipts first-party code is now licensed under [MIT](LICENSE), selected by the maintainer on 2026-11-06. Third-party components retain their own licenses; the frozen reference and upstream notices/hashes are preserved.

The development reference bundles junitparser 5.0.3 in its original wheel. The upstream license is retained in the wheel and copied to [junitparser-LICENSE.txt](docs/junitparser-LICENSE.txt). It is a development dependency, not a proposed Go runtime dependency.

The four small original report fixtures come from jenkinsci/junit-plugin. Their upstream [license](testdata/upstream/LICENSE) and [commit/URL provenance](testdata/upstream/provenance.json) are retained. Some development recordings copy two of these reports; they remain upstream fixtures, not newly observed consecutive runs. Other small recording fixtures were authored for this handoff.

Historical metrics are copied evidence, not raw third-party CI artifacts. The large original archives are excluded.
