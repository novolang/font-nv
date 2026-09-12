# Changelog

All notable changes to font-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

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
