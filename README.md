# font-nv

TrueType and OpenType are font file formats, specified together as
[OpenType](https://learn.microsoft.com/typography/opentype/spec/) and
standardised as ISO/IEC 14496-22. This package reads one in novo-lang: the
table directory, the metrics, the character-to-glyph map, the glyph outlines
in both outline formats, kerning, ligatures, and a shaper for Latin text. A
glyph outline comes back as [svg-nv](https://novo-lang.org/packages/svg-nv)'s
path type, and the transforms and rectangles are
[geometry-nv](https://novo-lang.org/packages/geometry-nv)'s.

**Status: NOT IMPLEMENTED — interface only.** Every function is declared with
its full signature, but every body is a `todo()` that panics when called. The
package is published so its design can be reviewed and depended on before it
is implemented. Version 0.1.0 will be the first working release.

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
| `GPOS` | positioning, including the modern kerning feature | the pair types |
| `GSUB` | substitution | ligatures and single substitution |

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

Build and test with `novo pkg build` and `novo test`. Today `novo test` fails
on purpose: every test reaches a `not implemented: font-nv.<module>.<fn>`
panic. The tests are the specification the implementation will have to
satisfy.

## What the package contains

| Module | Contents |
| --- | --- |
| `fontsrc` | The range type, the arithmetic over it, and the `FontSource` trait a host implements to hand bytes back. |
| `fontdir` | The table directory: the four sfnt version words, tags as integers, collections, the required tables per outline format, and the sfnt checksum. |
| `fontmetric` | `head`, `hhea`, `maxp`, `hmtx` and `OS/2` parsed, the three vertical metric sets, and the transform from font units to pixels. |
| `fontcmap` | The subtable list, the published preference order, formats 4 and 12 parsed, and the lookup from a character to a glyph number. |
| `fontglyf` | `loca` with its entry width carried on the value, quadratic outlines with the implied on-curve points restored, and composite glyphs answered as component records. |
| `fontcff` | The CFF INDEX and top dictionary, the subroutine bias, and a Type 2 charstring interpreter whose covered and refused operators are both published lists. |
| `fontkern` | One kerning source chosen once, from `GPOS` or from `kern`, with the pairs and the class tables gathered into a plan. |
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
16. **A subtable is picked, not merged.** A `cmap` holds several subtables for
    several platform encodings and they do not agree: a symbol font's subtable
    maps `U+F041` rather than `A`. `fontcmap.best_subtable` picks one by the
    order `preference_order` publishes, and the pick is visible in the value.
17. **What this package refuses is published as data, not as prose.**
    `fontcmap.formats_refused`, `fontcff.operators_refused`,
    `fontkern.gpos_lookup_types_refused` and `fontgsub.lookup_types_refused`
    are lists a caller can read, so they cannot drift from the code.
18. **`fonterror.severity` says how much text a fault costs.** A caller
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
- **Rasterising.** This package answers outlines.
  [raster-nv](https://novo-lang.org/packages/raster-nv) fills them.
- **`cmap` formats 0, 2, 6, 8, 10, 13 and 14.** `fontcmap.formats_refused`
  lists them. Format 14 carries variation selectors and is the one a text
  renderer eventually wants.
- **CFF `flex`, `seac` and the arithmetic operators.**
  `fontcff.operators_refused` lists them. They are not equal: `flex` is a
  curve-smoothing pair that shipped fonts use, and its absence loses a shallow
  curve.
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
novo test tests/fontdir_tests.nv      # magics, tags, ranges and the two checksums
novo test tests/fontcmap_tests.nv     # the lookup, and glyph 0
novo test tests/fontglyf_tests.nv     # loca's entry width, and composites
novo test tests/fontcff_tests.nv      # the subroutine bias and the interpreter's scope
novo test tests/fontshape_tests.nv    # metrics, kerning, ligatures and the refusal
novo test tests/fontsurface_tests.nv  # every entry point, with the types it declares
```

The reference implementation for the surface is
[ttf-parser](https://github.com/RazrFalcon/ttf-parser), which reads a font
without allocating. `fontTools` is the reference for the parts a reader
argues about. FreeType is the behavioural reference: where this package and
FreeType disagree about a glyph, FreeType is right.

The expected values are the OpenType specification's own worked examples: the
format 4 `cmap` with its segments and its terminator, the `hmtx` last-advance
rule, the four sfnt version words, the 12-plus-16n offset table arithmetic,
and the CFF subroutine bias thresholds. A test font is assembled byte by byte,
a directory in front of the tables it names, which is the same fixture shape
ttf-parser's own suite uses.

`fontsurface_tests.nv` reaches every entry point with the types the package
itself produces. An interface package's claim is that its signatures compose,
and a missing accessor or a type that cannot be constructed from outside is a
compile error in that file rather than a discovery in the first consumer.

The tests compile today and fail at run, each on the
`not implemented: font-nv.<module>.<fn>` panic that is its body. That is the
expected state of an interface release. They turn green one at a time as
bodies land. `novo test --isolate tests/<file>` prints one verdict per test.

## Implementation status

| Item | Implemented |
| --- | --- |
| `fontsrc.FontRange`, `.FontSource` | the type and the trait are declared; nothing constructs one |
| `fontsrc.range`, `.empty`, `.is_empty`, `.range_end`, `.range_fits`, `.sub`, `.slice` | no |
| `fontsrc.enough`, `.short` | no |
| `fontdir.FontFlavour`, `.FontTable`, `.FontFace` | the types are declared; nothing constructs one |
| `fontdir.header_len`, `.directory_len`, `.header_range`, `.directory_range` | no |
| `fontdir.table_count_of`, `.is_sfnt`, `.flavour`, `.flavour_of`, `.parse_directory` | no |
| `fontdir.is_collection`, `.collection_faces`, `.collection_header_range`, `.collection_face_at` | no |
| `fontdir.tag`, `.tag_of`, `.tag_name`, `.tags_for_text`, `.required_tags`, `.missing_required` | no |
| `fontdir.tag_head`, `.tag_hhea`, `.tag_hmtx`, `.tag_maxp`, `.tag_cmap`, `.tag_loca`, `.tag_glyf` | no |
| `fontdir.tag_cff`, `.tag_os2`, `.tag_kern`, `.tag_gpos`, `.tag_gsub` | no |
| `fontdir.table_range`, `.has_table`, `.table_count`, `.table_at`, `.table_tags`, `.ranges_fit`, `.checksum` | no |
| `fontmetric.FontHead`, `.FontHhea`, `.FontMaxp`, `.FontOs2`, `.FontHMetrics` | the types are declared; nothing constructs one |
| `fontmetric.FontMetrics`, `.FontAscent`, `.FontLineMetrics` | the types are declared |
| `fontmetric.parse_head`, `.parse_hhea`, `.parse_maxp`, `.parse_os2`, `.metrics` | no |
| `fontmetric.h_metrics`, `.advance_of`, `.hmtx_len`, `.is_monospaced` | no |
| `fontmetric.line_metrics`, `.ascent_recommended`, `.line_height`, `.ascent_sets_disagree` | no |
| `fontmetric.descender_sign_is_wrong`, `.has_x_height`, `.has_cap_height`, `.style_disagrees`, `.head_flag` | no |
| `fontmetric.scale_for_px`, `.scale_for_px_y_up`, `.units_to_px`, `.px_to_units`, `.ppem_for_points`, `.px_bounds` | no |
| `fontcmap.FontCmapSub`, `.FontCmap` | the types are declared; nothing constructs one |
| `fontcmap.header_len`, `.subtable_count`, `.list_range`, `.subtables`, `.best_subtable`, `.preference_order` | no |
| `fontcmap.is_readable`, `.formats_covered`, `.formats_refused`, `.parse_subtable` | no |
| `fontcmap.glyph_for`, `.has_codepoint`, `.glyphs_for` | no |
| `fontcmap.mapped_count`, `.covered_ranges`, `.max_codepoint`, `.covers_astral` | no |
| `fontglyf.FontLoca`, `.FontGlyphKind`, `.FontComponent` | the types are declared; nothing constructs one |
| `fontglyf.component_limit`, `.loca_len`, `.parse_loca`, `.loca_glyph_count` | no |
| `fontglyf.glyph_range`, `.glyph_file_range`, `.glyph_kind`, `.contour_count`, `.point_count` | no |
| `fontglyf.outline`, `.glyph_bounds`, `.bounds_from_points` | no |
| `fontglyf.components`, `.compose`, `.metrics_component`, `.component_glyphs`, `.names_itself` | no |
| `fontcff.FontCffIndex`, `.FontCffTop`, `.FontCharWidth` | the types are declared; nothing constructs one |
| `fontcff.header_len`, `.index_at`, `.index_entry`, `.index_end`, `.parse_top` | no |
| `fontcff.glyph_count`, `.charstring_range`, `.bias`, `.charstring_outline`, `.charstring_width` | no |
| `fontcff.call_depth_limit`, `.stack_limit`, `.operators_covered`, `.operators_refused` | no |
| `fontcff.operator_name`, `.is_interpretable`, `.is_cff2` | no |
| `fontkern.FontKernSource`, `.FontKernPair`, `.FontKernTable`, `.FontKernPlan` | the types are declared; nothing constructs one |
| `fontkern.kern_source`, `.has_both_sources`, `.plan`, `.no_kerning` | no |
| `fontkern.kern_subtable_count`, `.kern_is_apple`, `.kern_pairs` | no |
| `fontkern.gpos_lookup_types_covered`, `.gpos_lookup_types_refused`, `.gpos_has_kern`, `.gpos_scripts` | no |
| `fontkern.pair_value`, `.run_values`, `.pair_count`, `.kerns_nothing` | no |
| `fontgsub.FontLigature`, `.FontSubst`, `.FontSubstPlan` | the types are declared; nothing constructs one |
| `fontgsub.lookup_types_covered`, `.lookup_types_refused`, `.default_features`, `.no_substitutions` | no |
| `fontgsub.features_present`, `.scripts_present`, `.has_feature`, `.plan` | no |
| `fontgsub.ligatures`, `.singles`, `.apply`, `.apply_mapped`, `.ligature_len`, `.changes_anything` | no |
| `fontshape.FontPlaced`, `.FontShaped`, `.FontPlan` | the types are declared; nothing constructs one |
| `fontshape.plan`, `.shape`, `.shape_codepoints`, `.measure`, `.measure_px`, `.fit_prefix` | no |
| `fontshape.is_simple_script`, `.first_complex`, `.script_of`, `.is_right_to_left` | no |
| `fontshape.glyph_count`, `.placed_at`, `.glyph_at_x`, `.cluster_at`, `.has_ligature` | no |
| `fontread.read_face`, `.read_face_count`, `.read_table`, `.read_tables` | no |
| `fontread.read_metrics`, `.read_cmap`, `.read_loca`, `.read_outline`, `.read_outlines` | no |
| `fontread.read_plan`, `.read_subst`, `.read_kerning` | no |
| `fontread.FontBuffer`, `.buffer` | the type is declared; `buffer` is not implemented |
| `fonterror.FontFault`, `.FontSeverity`, and the `Error` implementation | the types are declared; `message` is not implemented |
| `fonterror.fault_table`, `.severity`, `.is_recoverable`, `.substitute_glyph`, `.describe` | no |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
