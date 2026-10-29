# font-nv

TrueType and OpenType are font file formats, specified together as
[OpenType](https://learn.microsoft.com/typography/opentype/spec/) and
standardised as ISO/IEC 14496-22. This package reads one in novo-lang: the
table directory, the metrics, the character-to-glyph map, the glyph outlines
in both outline formats, kerning, ligatures, and a shaper for Latin text. A
glyph outline comes back as [svg-nv](https://novo-lang.org/packages/svg-nv)'s
path type, and the transforms and rectangles are
[geometry-nv](https://novo-lang.org/packages/geometry-nv)'s.

## What it is

A font file is an **index**, not a document. Twelve bytes say how many tables
it has. Sixteen bytes per table say where each one lives. Everything after
that is independent, so drawing a line of English reads four tables out of the
twenty a modern font carries.

A **face** is one font inside a file. A **collection** holds several faces in
one file, sharing tables between them. A **table** is named by a four-letter
**tag**, and a tag is stored as the four bytes packed into one integer.

A **glyph** is one shape the font can draw, named by a number rather than by a
character. The **cmap** table maps a character to a glyph number. Glyph 0 is
`.notdef` in every conformant font: the hollow box a reader recognises as a
missing character.

Outlines come in two formats. **TrueType outlines**, in the `glyf` table, are
quadratic curves, and the `loca` table says where each glyph's outline
begins. **CFF outlines**, in the `CFF ` table, are cubic curves written as a
small stack program called a **charstring**. A **composite glyph** is one
built from other glyphs with a transform on each, which is how an accented
letter is stored once as a letter and once as an accent.

Every number in a font is in **font units**. There are `unitsPerEm` of them to
an em, which is 1000 in a CFF font and 2048 in most TrueType ones. A font unit
is not a pixel.

**Shaping** is turning a string into glyphs with positions. Three things
happen: the characters become glyph numbers, **substitutions** replace
sequences with other glyphs (which is what a ligature is), and **kerning**
adjusts the space between particular pairs.

| Table | What it holds | Read here |
| --- | --- | --- |
| `head` | units per em, the design bounding box, the `loca` format | yes |
| `hhea` | the horizontal line metrics and the `hmtx` entry count | yes |
| `maxp` | the glyph count and the composite depth limit | yes |
| `hmtx` | each glyph's advance width and left side bearing | yes |
| `OS/2` | a second and third set of vertical metrics, x-height, cap height | yes |
| `cmap` | characters to glyph numbers | formats 4 and 12 |
| `loca` | where each glyph's outline begins | yes |
| `glyf` | quadratic outlines and composites | yes |
| `CFF ` | cubic outlines as charstrings | yes |
| `kern` | the legacy pair kerning table | horizontal format 0 |
| `GPOS` | positioning, including the modern kerning feature | pair adjustment, directly or behind an extension lookup |
| `GSUB` | substitution | ligatures and single substitution, directly or behind an extension lookup |

| Quantity | Value |
| --- | --- |
| Bytes in the offset table | 12 |
| Bytes per directory row | 16 |
| Tables read to draw a line of Latin text | 4 |
| sfnt version words accepted | 4 |
| Glyph number of `.notdef` | 0 |
| Font units per em, CFF | 1000 |
| Font units per em, most TrueType fonts | 2048 |
| CFF subroutine bias thresholds | 107, 1131, 32768 |

## Install

```
novo pkg add font-nv
```

## Example

```novo
use std.bytes
use fontdir
use fontgsub
use fontread
use fontshape

fn main() [io]
    // A font file the caller already holds. This package reads nothing
    // itself: `buffer` is the source that costs no effects at all.
    let src = fontread.buffer(bytes.zeros(0))

    // The first face's table directory. It carries no font bytes, so it
    // is a few hundred bytes whatever the file's size.
    match fontread.read_face(src, 0)
        Err(f) => println(f.message())
        Ok(face) =>
            // The four tables a Latin run needs, gathered into one plan.
            match fontread.read_plan(src, face, fontdir.tag_of("latn"),
                                     fontgsub.default_features())
                Err(f) => println(f.message())
                Ok(p)  =>
                    // How wide the run is at 16 pixels per em, rounded once
                    // at the end rather than once per glyph.
                    match fontshape.measure_px(p, "Waffle", 16.0)
                        Ok(w)  => println("${w}")
                        Err(f) => println(f.message())
```

Build and test with `novo pkg build` and `novo test`.

## What the package contains

| Module | Contents |
| --- | --- |
| `fontsrc` | The range type, the arithmetic over it, and the `FontSource` trait a host implements to hand bytes back. |
| `fontdir` | The table directory: the four sfnt version words, tags as integers, collections, the required tables per outline format, and the sfnt checksum. |
| `fontmetric` | `head`, `hhea`, `maxp`, `hmtx` and `OS/2` parsed, the three vertical metric sets, and the transform from font units to pixels. |
| `fontcmap` | The subtable list, the published preference order, formats 4 and 12 parsed, and the lookup from a character to a glyph number. |
| `fontglyf` | `loca` with its entry width carried on the value, quadratic outlines with the implied on-curve points restored, and composite glyphs answered as component records. |
| `fontcff` | The CFF INDEX and top dictionary, the subroutine bias, and a Type 2 charstring interpreter whose covered and refused operators are both published lists. |
| `fontkern` | One kerning source chosen once, from `GPOS` or from `kern`, with the pairs and the class matrices gathered into a plan. |
| `fontgsub` | Ligatures and single substitution, with the feature tags the caller's to name. |
| `fontshape` | A run of text into placed glyphs: the plan, the shaping, the measurement, the cluster map, and the refusal for scripts this package will not lay out. |
| `fontread` | Twelve loops over a `FontSource`, each written once, and `FontBuffer`, the source over a buffer that costs nothing. |
| `fonterror` | Sixteen faults, each naming the table it came from, and the severity that says how much text each one costs. |

## How to choose an entry point

**`fontread.buffer` is the way in for a caller holding the whole file.** It
wraps a buffer as a `FontSource` and costs no effects at all, so the common
case writes no implementation.

**A `FontSource` implementation is the way in for a caller holding a file, a
socket or a flash page.** It is one method: given a range, answer those bytes.
Everything in `fontread` is then charged exactly what that implementation
costs, and this package stays free of effects either way.

**`fontread.read_plan` is the way in for text.** It reads the four tables a
Latin run needs and gathers them, and `fontshape.shape` turns a string into
placed glyphs.

**`fontshape.measure` and `measure_px` answer a width without building the
placements.** A layout pass that only needs to know whether a line fits calls
those.

**`fontread.read_outlines` is the way in for a glyph atlas.** It takes a list
of glyph numbers and reads them in one sorted pass.

**The parsing functions stand alone for a caller who has the table bytes
already.** `fontmetric.parse_head`, `fontcmap.parse_subtable`,
`fontglyf.outline` and the rest take bytes and answer values, with no source
in sight.

## The rules a user needs

1. **This package reads nothing.** Every answer about where something is, is a
   range. A caller holding the file cuts it out with `fontsrc.slice`; a caller
   holding nothing implements `FontSource` and the package's read loops are
   charged whatever that costs.
2. **The standard library's `Read` and `Seek` cannot describe a seekable
   source together.** A function binds exactly one effect parameter, so
   `<S: Read[e] + Seek[e]>` is `E3005`. That is why the trait here is this
   package's own, and it is a single method taking a range.
3. **A character the font does not have answers glyph 0, never `None`.** Glyph
   0 is `.notdef`, it has an advance like any other glyph, and drawing it is
   what a reader recognises. An optional would invite a caller to skip the
   character, which silently shortens the line and reports nothing.
   `fontcmap.has_codepoint` is the separate question about coverage.
4. **Outlines and advances come out in font units, and nothing converts for
   the caller.** `fontmetric.scale_for_px` answers the one transform that maps
   them to pixels. A rasteriser caches one outline per glyph and draws it at
   any size, and a shaper accumulates advances and rounds once. Rounding per
   glyph is visibly the wrong line length by the fortieth character.
5. **That transform flips the y axis.** A font's y grows up from the baseline
   and an image's grows down. `fontmetric.scale_for_px_y_up` is the version
   without the flip, for a caller whose own space already grows upward.
6. **There is no `ascender`, because a font records one three times.**
   `hhea.ascender`, `OS/2.sTypoAscender` and `OS/2.usWinAscent` disagree in a
   great many shipped fonts by enough to change how many lines fit on a page.
   `fontmetric.line_metrics` takes a `FontAscent` and has no default, because
   the default is the bug. `ascent_recommended` answers which set the font
   itself asks for, and `ascent_sets_disagree` reports the condition.
7. **`hmtx` does not have one entry per glyph.** A monospaced font stores
   exactly one, and every glyph past `hhea.numberOfHMetrics` takes the last
   advance. `fontmetric.h_metrics` applies that rule.
8. **Kerning has one source and never two.** A font may carry both a legacy
   `kern` table and a `GPOS` kerning feature with the same pairs in each.
   Applying both moves the letters twice, and the result is text that is
   subtly too tight on every line. `fontkern.kern_source` chooses,
   `FontKernPlan` carries the choice, and no call reads both.
   `fontkern.has_both_sources` is published so a validator can report it.
9. **`loca`'s entries are two bytes or four, and the field that decides is in
   `head`.** A short `loca` read as long gives every glyph the wrong offset,
   which parses as noise rather than failing. `FontLoca` carries the format on
   the value, so a caller cannot lose it between the two reads.
10. **A composite glyph is answered, not followed.** `fontglyf.components`
    hands back the component records, because following them means reading and
    reading is the host's half. `fontread.read_outline` is the loop that does
    follow them, over a `FontSource`.
11. **A component record is a 2 by 3 affine matrix**, which is
    geometry-nv's `GeomXform`. A glyph's bounding box is its `GeomRectF`.
    Declaring a second matrix type here would put two incompatible ones in one
    program, which the compiler refuses at the consumer with `E2004`.
12. **The CFF subroutine bias is 107, 1131 or 32768, by how many subroutines
    the INDEX holds.** It applies to the local and global INDEXes
    independently. A reader that hard-codes 107 draws correct glyphs in a small
    font and nonsense in a large one, which passes every test written against a
    small test font.
13. **The `CFF ` tag has a trailing space and the `OS/2` tag has a slash.**
    Both are part of the four bytes. `fontdir.tag_cff` and `tag_os2` spell them
    so a hand-written comparison does not.
14. **`fontshape.shape` refuses a run containing a complex script.** Arabic
    joins, Devanagari reorders and Thai stacks, and none of that is done here.
    The refusal is `FontComplexScript` carrying the codepoint, because text
    laid out in isolated forms is unreadable text that looks like text, and a
    caller would ship it. `fontshape.first_complex` asks in advance.
15. **Nothing here reorders bidirectional text.** The Unicode bidirectional
    algorithm runs on characters before a font is chosen.
    `fontshape.is_right_to_left` names the property so a caller can route.
16. **A script the font does not declare falls back to `DFLT`.** A font that
    lists its features under `DFLT` alone still kerns and ligates a Latin run,
    as OpenType specifies. An unlisted script and no `DFLT` finds no feature.
17. **A ligature is chosen by the font's order, not by its length.** Two
    ligatures that start with the same glyph are tried in the order the font
    lists them, and the first that matches wins. A font lists `ffi` before
    `fi` when it wants `ffi`.
18. **Kerning adds across lookups and stops within one.** The `kern` feature
    names lookups, and every lookup adjusts a pair on its own. Within one
    lookup the first sub-table that gives the pair a non-zero value decides,
    which is how HarfBuzz reads a class matrix whose first sub-table covers
    the glyph with a zero.
19. **A subtable is picked, not merged.** A `cmap` holds several subtables for
    several platform encodings and they do not agree: a symbol font's subtable
    maps `U+F041` rather than `A`. `fontcmap.best_subtable` picks one by the
    order `preference_order` publishes, and the pick is visible in the value.
20. **What this package refuses is published as data, not as prose.**
    `fontcmap.formats_refused`, `fontcff.operators_refused`,
    `fontkern.gpos_lookup_types_refused` and `fontgsub.lookup_types_refused`
    are lists a caller can read, so they cannot drift from the code.
21. **`fonterror.severity` says how much text a fault costs.** A caller
    deciding between falling back to another font and giving up on text reads
    it, and `is_recoverable` and `substitute_glyph` are the two follow-up
    questions.

## What is not included

- **Complex script shaping.** Arabic joining, Indic reordering and mark
  attachment need state this package does not carry. That is HarfBuzz's
  subject, and a binding over it is the way to get it.
- **The Unicode bidirectional algorithm.** It runs before a font is chosen and
  belongs in a Unicode package.
- **Hinting.** The TrueType instruction set is a virtual machine whose job is
  moving points at small sizes, and CFF's hint operators are read and not
  acted on. What that costs is bitmap quality below about 11 pixels per em.
- **GPOS lookups other than pair adjustment.** Mark attachment, cursive
  attachment and contextual positioning are not applied, and a lookup of
  those types in the `kern` feature adds nothing.
  `fontkern.gpos_lookup_types_refused` lists them.
- **Rasterising.** This package answers outlines.
  [raster-nv](https://novo-lang.org/packages/raster-nv) fills them.
- **`cmap` formats 0, 2, 6, 8, 10, 13 and 14.** `fontcmap.formats_refused`
  lists them. Format 14 carries variation selectors and is the one a text
  renderer eventually wants.
- **CFF `flex`, `seac` and the arithmetic operators.**
  `fontcff.operators_refused` lists them. They are not equal: `flex` is a
  curve-smoothing pair that shipped fonts use, and its absence loses a shallow
  curve.
- **CID-keyed CFF fonts.** A CID-keyed font keeps its subroutines in one
  private dictionary per font dictionary and picks the dictionary for a glyph
  with an FDSelect. Neither is read, so `parse_top` reports `is_cid` and a
  charstring that calls a local subroutine is refused with
  `FontCharstringState`. Most CJK fonts in OpenType form are of this kind.
- **CFF2 and sfnt-wrapped Type 1.** Both are refused by name. A CFF2 outline
  is a function of design axes rather than a shape, and reading one as CFF
  produces plausible garbage.
- **Variable fonts.** A variable font's default instance reads correctly here.
  A named instance does not exist until the deltas are applied.
- **Bitmap and colour tables.** An emoji font read here answers outlines where
  it has them and `.notdef` where its glyphs are pictures.
- **WOFF and WOFF2.** A WOFF2 file is the same tables in a Brotli-compressed
  container. This package reads the container it is handed and decompresses
  nothing, because a font reader that also decompressed would make every
  consumer download a decompressor to read a `.ttf` off disk.
- **A device build.** There is no `tests/embedded_probe.nv` and no claim that
  any module runs on a microcontroller. A firmware with a display ships a
  pre-rasterised bitmap font, because a parser plus a rasteriser is tens of
  kilobytes to draw text whose shape the device already knows.
- **Character properties.** `fontshape.script_of` uses the coarse ranges it
  needs to pick an OpenType script tag. It is not a substitute for a Unicode
  character database.

## Related packages

- [svg-nv](https://novo-lang.org/packages/svg-nv) owns the path type. A glyph
  outline is a move, some lines, some quadratic curves and a close, and
  `SvgQuadTo` keeps the control point exact, which is what TrueType needs.
- [geometry-nv](https://novo-lang.org/packages/geometry-nv) owns the affine
  transform and the rectangle. See rule 11.
- [raster-nv](https://novo-lang.org/packages/raster-nv) fills the outlines this
  package answers, which is how a glyph becomes pixels.
- `std.text` in the standard library draws text through a C library. This
  package plus a rasteriser is the same path with no C library in it, which is
  what lets it build for WebAssembly.

## Tests

```bash
novo test                          # every suite
bash tests/coverage.sh             # the line coverage over src/, merged across the suites
bash tests/oracle/compare.sh       # this package against HarfBuzz and FreeType, on installed fonts
```

The suites fall in three groups. `fontdir_tests.nv`, `fontcmap_tests.nv`,
`fontglyf_tests.nv`, `fontcff_tests.nv`, `fontshape_tests.nv` and
`fontsurface_tests.nv` assert what each table means. `font_edge_tests.nv` and
the `*_edge_tests.nv` files read every table field by field from fonts
assembled byte by byte in the test, so each fixture differs from a good table
in the one field the case names. `hostile_tests.nv`, `font_gap_tests.nv` and
`font_layout_gap_tests.nv` hold the inputs that are cut short, claim more than
they contain or repeat themselves, and the branches only those reach.

The expected values are the OpenType specification's own worked examples: the
format 4 `cmap` with its segments and its terminator, the `hmtx` last-advance
rule, the four sfnt version words, the 12-plus-16n offset table arithmetic,
and the CFF subroutine bias thresholds. A test font is assembled byte by byte,
a directory in front of the tables it names, which is the same fixture shape
ttf-parser's own suite uses.

`tests/oracle/compare.sh` shapes five lines of text in thirteen installed
fonts, with and without the `liga` feature, once through this package and once
through HarfBuzz, and compares the glyph numbers, each glyph's pen position and
the run's width. FreeType loads each glyph unscaled and the control box of its
outline is compared with this package's. The fonts include TrueType and CFF
outlines, `kern` tables and `GPOS` kerning in class and listed form, extension
lookups, and one face of a collection. Where this package and FreeType or
HarfBuzz disagree about a glyph, they are right.

`fontsurface_tests.nv` reaches every entry point with the types the package
itself produces. A missing accessor or a type that cannot be constructed from
outside is a compile error in that file rather than a discovery in the first
consumer.

`tests/coverage.sh` merges the line coverage of the suites over `src/` and
exits non-zero below 100%.

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
