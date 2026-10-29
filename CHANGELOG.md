# Changelog

All notable changes to font-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.1.0 — 2026-10-29

The first implementation of the interface published as 0.0.3: every function
has a body.  The package is read, tested and measured against HarfBuzz and
FreeType on installed fonts, and the line coverage over `src/` is 100%.

### Breaking

These break code written against 0.0.x.

- `FontKernPlan` has two new fields, `later_matrices` and `matrix_lookups`, and
  the new type `FontKernMatrix` holds one class matrix.  A font splits its
  class kerning across several sub-tables, so one set of class fields cannot
  hold it.  Code that builds a `FontKernPlan` by hand adds both fields.
- `FontKernPair` has a new field, `lookup`, the number of the `kern` lookup
  that listed the pair.  The adjustments of different lookups add.
- `fontgsub.lookup_types_refused` is `[2, 3, 5, 6, 8]` and
  `fontkern.gpos_lookup_types_refused` is `[1, 3, 4, 5, 6, 7, 8]`.  Extension
  lookups (`GSUB` 7, `GPOS` 9) are read as the lookup they wrap, so they are no
  longer refused.
- The ligatures of a `FontSubstPlan` are ordered by first glyph and then by the
  order the font lists them, not by length.  A font that lists `fi` before `ffi`
  gets `fi`, as HarfBuzz gives.
- `FontSubstPlan.features` holds the requested features the font declares for
  the script, not every feature requested.
- A script the font does not declare falls back to `DFLT` and `dflt`, as
  OpenType specifies, in `fontgsub` and `fontkern`.
- The class arrays of a `FontKernPlan` hold -1 for a left glyph its coverage does
  not name and for a right glyph its class definition leaves unnamed.
- The table offsets of a face in a collection count from the start of the file,
  as the collection format defines them.  `fontdir.parse_directory` adds its `at`
  argument to each offset, and `fontread.read_face` passes 0.
- `fontread.read_cmap` reads the whole `cmap` table once instead of the header
  and one subtable.
- `fontglyf.components` reads the 2 by 2 transformation of a composite as
  FreeType does: the second number scales x into y, the third y into x.

### Added

- Bodies for `fontsrc`, `fontdir`, `fonterror`, `fontmetric`, `fontcmap`,
  `fontglyf`, `fontcff`, `fontgsub`, `fontkern`, `fontshape` and `fontread`.
- The `FontBuffer` source, which costs no effects.
- A work limit on a charstring's subroutine calls, on a plan's substitutions and
  pairs, and on the records one composite outline reads, so a font built to
  fan out is refused rather than followed.
- `tests/coverage.sh`, and `tests/oracle/`, which compares this package with
  HarfBuzz and FreeType on installed fonts.

### Not read

- CID-keyed CFF fonts keep their subroutines per font dictionary, selected by an
  FDSelect.  Neither is read, so a charstring of such a font that calls a local
  subroutine is refused with `FontCharstringState`.

## 0.0.3 — 2026-09-28

The dependency ranges move to the dependencies' current releases.  A
pre-1.0 caret range admits only the release it names, so the old
ranges held this package on interface releases, and a program could
not take this package beside those packages' current releases.  No
signature in this package changed.

- geometry-nv: `^0.0.1` to `^0.1.0`.
- svg-nv: `^0.0.1` to `^0.1.0`.

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
