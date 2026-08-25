# Offline dependency notices

The optional operating-system offline packs redistribute the unmodified wheel files listed below. Every wheel remains intact, including its embedded metadata and license files. The light plugin archive contains none of these third-party wheels.

| Distribution | Version | License | Upstream |
| --- | ---: | --- | --- |
| Pillow | 12.3.0 | MIT-CMU | https://github.com/python-pillow/Pillow |
| PyYAML | 6.0.3 | MIT | https://github.com/yaml/pyyaml |
| python-pptx | 1.0.2 | MIT | https://github.com/scanny/python-pptx |
| XlsxWriter | 3.2.9 | BSD-2-Clause | https://github.com/jmcnamara/XlsxWriter |
| lxml | 6.0.2 | BSD-3-Clause with bundled-library notices inside the official wheel | https://github.com/lxml/lxml |
| typing-extensions | 4.15.0 | PSF-2.0 | https://github.com/python/typing_extensions |

The official Pillow and lxml wheels may contain compiled third-party libraries. Their applicable notices remain inside the wheel archives and must not be removed when redistributing an offline pack. The generated `offline-pack.json` and `requirements.lock` record exact files and SHA-256 hashes.
