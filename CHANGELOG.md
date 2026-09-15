# Changelog

All notable changes to font-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.0.2 — 2026-09-15

- README rewritten to the package README style guide (docs/writing-a-readme.md); no change to the interface.

## 0.0.1 — 2026-09-11

The **interface**: every signature and every effect row, and no bodies.
`stability = "draft"`, and the release is recorded `implemented = false`.

### Added

- `fontsrc` — `FontRange`, the `FontSource[e]` trait, and the range
  arithmetic every parser opens with.
- `fontdir` — `FontFace` as a directory and no font bytes, the four
  sfnt magics, tags as integers, TrueType collections, and the `head`
  checksum exception.
- `fontmetric` — `head`, `hhea`, `maxp` and `OS/2` parsed, `hmtx`'s
  last-advance rule, the three ascent sets with no default, and
  `scale_for_px`.
- `fontcmap` — subtable selection by a published order, formats 4 and
  12, and `glyph_for` answering `.notdef`.
- `fontglyf` — `loca` with its format carried on the value, quadratic
  outlines with the implied on-curve points restored, and composites
  answered rather than followed.
- `fontcff` — the INDEX and the top DICT, the subroutine bias, and a
  Type 2 interpreter whose scope is two published lists.
- `fontkern` — one kerning source, chosen once, from `GPOS` or `kern`.
- `fontgsub` — ligatures and single substitution, with the feature set
  the caller's to name.
- `fontshape` — `FontPlaced`, `FontShaped` and the cluster map, and a
  refusal for complex scripts.
- `fontread` — twelve effect-polymorphic loops and `FontBuffer`, the
  impl that costs nothing.
- `fonterror` — seventeen refusals, and `severity` saying how much text
  each one costs.

### Known

- **`FontSource[e]` is the load-bearing interface**, and the argument
  is that a font is an index: four tables out of twenty are read to
  draw a line of English, and the trait is what lets the dependent-read
  loop live in the package without the package performing a read.
- **The two standard-library traits cannot describe a seekable
  source.** `<S: Read[e] + Seek[e]>` is `E3005` — a function binds
  exactly one effect parameter — which is why the trait is this
  package's own.
- **A missing character is glyph 0 and never `None`**, so a caller's
  `match` cannot silently shorten a line.
- **Outlines are in font units** and `scale_for_px` is a separate call,
  so a rasteriser can cache per glyph and a shaper can round once.
- **Kerning has one source**, because a font with both tables kerned
  twice is text that is wrong on every line and looks nearly right.
- **Complex scripts are refused by name**, not approximated;
  `libharfbuzz-sys` is the shelf row that covers them.
- **The path type comes from svg-nv** because geometry-nv has none, and
  the README says why that is the wrong home for it.
- **No device claim.** A firmware with a display ships a bitmap font;
  a claim with no consumer is a claim nobody maintains.
- The scaffold's `src/font.nv` was dropped for eleven prefixed modules.

### Design notes

Three findings recorded here rather than in the README, which states what the
package does rather than how it was decided. The manifest's comment on the
`svg-nv` dependency points at a README section that the 0.0.2 rewrite removed;
the first note below is that section.

- **The path type is in the wrong package, for the right reason.** A glyph
  outline is a move, some lines, some quadratic curves and a close, and the
  only typed path on the registry is svg-nv's. geometry-nv has no path type at
  all: it stops at `GeomPoly`, a closed list of points, which cannot hold a
  curve. So a font reader and a rasteriser both depend on an XML writer in
  order to agree on four curve commands. `SvgPath`, `SvgPathCmd` and
  `SvgSubpath` describe geometry rather than SVG, and moving them into
  geometry-nv with svg-nv re-exporting them is a one-package change this row
  would take the day it lands; nothing here would change but a `use` line.
  Declaring a `FontPath` instead is worse, because a rasteriser would then
  have to accept two path types that mean the same thing.
- **WOFF2 is a real row and its parts are named.** A web font on the wire is
  WOFF2: the same sfnt tables in a Brotli-compressed container. The parts it
  needs are this package's table directory, a Brotli decoder, and the format's
  own glyph-record transform, which is the only genuinely new work. It is not
  in this package because a font reader that also decompressed would make every
  consumer download a decompressor to read a `.ttf` off disk.
- **This package plus a rasteriser replaces a FreeType binding.** A terminal
  building a glyph atlas today goes through a foreign-function trampoline over
  FreeType, with a fallback that draws stripes when the C library is missing.
  Reading the 95 printable ASCII outlines here and filling them with raster-nv
  is the same path natively. What it buys is not speed — FreeType is faster —
  it is that drawing a character needs no C library and that the whole path
  builds for WebAssembly.
