# Attribution and licenses

New integration/tooling/documentation: created by an LLM (OpenAI Codex), distributed under this repository's MIT license. This does not replace the authorship or licenses of the following projects. This list covers both related repositories; some entries are used only by the graphics project or only by the converter, as noted below.

- [OpenGothic](https://github.com/Try/OpenGothic), by Try and contributors â€” MIT.
- [OpenGothic-Android](https://github.com/borsuczyna/OpenGothic-Android), the Android fork used as the integration base â€” MIT; retain its own notices and those of its dependencies.
- [Tempest](https://github.com/Try/Tempest) â€” retain the license supplied by its pinned source tree. Used by the graphics project; its patch is an addition to the Android fork's existing Tempest patches.
- [ZenKit](https://github.com/GothicKit/ZenKit), by GothicKit contributors â€” MIT. The converter fetches its source and applies a small packed-inventory parsing fix.
- [libadrenotools](https://github.com/bylaws/libadrenotools), by Billy Laws â€” BSD-2-Clause; used by the separate graphics loader.
- [liblinkernsbypass](https://github.com/bylaws/liblinkernsbypass) â€” retain its supplied license; used through libadrenotools.
- [Mesa](https://www.mesa3d.org/), including Turnip â€” see [Mesa's licensing information](https://docs.mesa3d.org/license.html) and the notices for the actual driver build. No Mesa driver binary is committed here.
- [K11MCH1/AdrenoToolsDrivers](https://github.com/K11MCH1/AdrenoToolsDrivers) â€” external distribution source for the tested Turnip build; not the author of the underlying Mesa driver code.
- [Khronos Vulkan-Headers](https://github.com/KhronosGroup/Vulkan-Headers) â€” retain the license supplied by its pinned source tree.

Downloaded source trees retain their own license files. Other transitive dependencies retain their licenses as well. No license to Gothic game assets, scripts, save contents, trademarks, or artwork is granted by this repository. Those files are not distributed here.

Copies of the principal upstream license notices are included in `licenses/`.
