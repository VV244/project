# Third-party notices

## Bootstrap 5.3.8

The self-hosted `static/vendor/bootstrap.min.css` is from the Bootstrap project
and uses the MIT license. Copyright and permission notice:
`static/vendor/licenses/bootstrap-LICENSE.txt`.
Source: https://github.com/twbs/bootstrap/tree/v5.3.8

## Bootstrap Icons 1.13.1

Self-hosted icon CSS and fonts use the MIT license. Notice: `static/vendor/licenses/bootstrap-icons-LICENSE.txt`. Source: https://github.com/twbs/icons/tree/v1.13.1

## Fonts

Self-hosted WOFF2 files in `static/fonts/` were obtained from Google Fonts’
distribution of Nunito and Noto families and converted from distributed TTF
files to WOFF2 without renaming the font families or changing glyph outlines.
No visitor font request goes to Google.

- Nunito
- Noto Sans Devanagari
- Noto Nastaliq Urdu
- Noto Sans Gujarati
- Noto Sans Tamil
- Noto Sans Telugu
- Noto Sans Kannada
- Noto Sans Malayalam
- Noto Sans Bengali (also used for Assamese)
- Noto Sans Gurmukhi
- Noto Sans Oriya

Each uses the SIL Open Font License 1.1. Full authorship/license notices are in
the corresponding `static/vendor/licenses/*-OFL.txt` files. Original source and
license catalogue: https://github.com/google/fonts/tree/main/ofl

## Synthetic demonstration narration

`demo_assets/pocketful-of-sunshine.mp3` was generated with the installed Flite
CMU US SLT voice through FFmpeg’s Flite filter, reading only the project’s
original English verse. Flite’s speech engine and voice notices are preserved
in `static/vendor/licenses/flite-copyright.txt` (including the CMU permissive
license and applicable component notices). Source: http://www.festvox.org/flite/

The Flite/FFmpeg executables are not bundled or required at application runtime.
FFmpeg produced the MP3 via libmp3lame. This file is explicitly identified as
synthetic narration in the sample poem’s editable attribution.

## Python dependencies

Python packages are declared and pinned in `requirements.txt`; their
distributions carry their own licenses. Do not treat the application’s MIT or
demo content’s CC0 dedication as replacing dependency licenses.

## New content

The demonstration contains no copied modern nursery rhymes and no sample
YouTube videos whose child suitability or permissions could not be verified.
Administrators may add properly licensed media. External providers retain
their rights and privacy terms.
