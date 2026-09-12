# font-nv

**Status: NOT IMPLEMENTED — interface only.**

Every public function below is published with its signature and its
effect row, and every body is `todo()`. Installing this package works;
calling it panics with `not implemented`.

## What this is

TrueType and OpenType, read as an **index** rather than as a file.
Glyph outlines, font metrics and a shaper for Latin text — the part of
FreeType that is arithmetic, with none of the part that is a C library.

- `fontsrc` — `FontRange` and the `FontSource[e]` trait; the seam;
- `fontdir` — the table directory, the four sfnt magics, tags,
  collections, checksums;
- `fontmetric` — `head`, `hhea`, `maxp`, `hmtx`, `OS/2`, and font
  units to pixels;
- `fontcmap` — `cmap` formats 4 and 12; characters to glyph ids;
- `fontglyf` — `loca` and `glyf`: quadratic outlines and composites;
- `fontcff` — the `CFF ` table and a scoped Type 2 charstring
  interpreter;
- `fontkern` — pair kerning, from `GPOS` **or** from `kern`;
- `fontgsub` — `GSUB` cut to ligatures and single substitution;
- `fontshape` — a line of Latin text, glyphs with positions;
- `fontread` — every loop, written once, over a `FontSource[e]`;
- `fonterror` — every refusal, and how much text it costs.

```
novo pkg add font-nv
novo pkg build
novo test
```

## The one example that will work

A terminal building its glyph atlas: open a font, read the four tables
a run of ASCII needs, and pull 95 outlines without reading the rest of
the file.

```novo ignore
use fontread
use fontdir
use fontmetric
use fontshape

// The four lines a host writes once.  Everything else in this package
// is charged what THIS costs and nothing more.
struct FontFile
    handle: File

impl FontSource[io] for FontFile
    fn font_bytes(self, r: FontRange) -> Result<Bytes, FontFault> [io]
        match self.handle.seek(SeekStart(r.at))
            Err(e) => Err(FontSourceFailed(e.message()))
            Ok(_)  =>
                match self.handle.read(r.len)
                    Err(e) => Err(FontSourceFailed(e.message()))
                    Ok(b)  => Ok(b)

fn build_atlas(path: Str, px: Float) -> Result<[SvgPath], FontFault> [io, fs]
    match File.open_read(path)
        None    => Err(FontSourceFailed("not found"))
        Some(f) =>
            let src = FontFile { handle: f }
            let face = fontread.read_face(src, 0)!
            let m    = fontread.read_metrics(src, face)!
            let cmap = fontread.read_cmap(src, face)!
            let loca = fontread.read_loca(src, face, m)!

            // 95 printable ASCII characters, through the cmap, in one
            // sorted pass over `glyf`.
            var wanted: [Int] = []
            var c = 32
            while c < 127
                wanted = list.push(wanted, fontcmap.glyph_for(cmap, c))
                c = c + 1
            fontread.read_outlines(src, face, loca, wanted)
```

## The load-bearing interface: `FontSource[e]`

```novo ignore
pub struct FontRange
    at: Int
    len: Int

pub trait FontSource[e]
    fn font_bytes(self, r: FontRange) -> Result<Bytes, FontFault> [e]

pub fn read_face<S: FontSource[e]>(src: S, index: Int)
                -> Result<FontFace, FontFault> [e]
```

**A font is an index, not a document.** Twelve bytes say how many
tables there are; sixteen bytes per table say where each one lives;
everything after that is independent. Drawing a line of English reads
four tables out of the twenty a modern font carries. Noto Sans CJK is
20 MB and a terminal draws ASCII out of it. A web page's font arrives
over a socket. Reading the whole file first should be a decision the
caller is allowed not to make.

So this package reads nothing and says **where** instead. `FontRange`
means two things at once: to a caller holding the file it is a span
into the buffer it already has, and to a caller holding nothing it is a
request — read these `len` bytes at `at`. `docs/publishing.md` § How a
`core` package takes bytes from its host calls the second one "the core
asks, the host performs".

**Why a trait and not only a range.** elf-nv stops at the range and
leaves the loop to the caller, which is right for ELF. A font's loop is
longer, and every step of it depends on the one before: the directory's
length is in the offset table, `loca`'s entry width is in `head`, the
glyph's offset is in `loca`, and a composite glyph's components are
found the same way again. Written by hand at each call site that is
twenty lines with four places to get an offset base wrong. The trait
lets `fontread` write it **once** without the package acquiring an
effect — the bound binds the trait's effect parameter and the clause is
`[e]`, so `read_face` costs `[io, fs]` over a `File` and nothing at all
over a buffer, and the package stays `core` either way.

**And the standard library's traits cannot express it.** A random-access
source is `Read` *and* `Seek`, and a function may bind exactly one
effect parameter: `<S: Read[e] + Seek[e]>` is `E3005`, with a message
saying a clause mixing two supplies could not say which name each one
filled. That is the right refusal — but it means the two stdlib traits
cannot describe a seekable source at all, so this package declares the
one trait that is random access by construction. `fontread.buffer` is
the zero-cost impl for the caller that does hold the whole file, so the
common case writes no impl at all.

## Three decisions worth arguing

### A missing character is glyph 0, never `None`

`fontcmap.glyph_for` answers an `Int`. A `cmap` lookup that finds
nothing is not an absence — it is the font saying "I have a glyph for
that, and it is the box". Glyph 0 is `.notdef` in every conformant
font, it has an advance like any other glyph, and drawing it is what a
reader recognises as a missing character.

An `?Int` would invite the three lines every caller writes next —
`match g { None => continue, Some(g) => draw(g) }` — and that `continue`
is text silently shortened: the character vanishes, the line comes out
narrower than the layout reserved, and nothing in the output says so.
Answering 0 makes the visible failure the default and the deliberate
skip the thing a caller has to write. `has_codepoint` is there for the
caller genuinely asking about coverage, which is a different question.

### Font units are not pixels, and the conversion is a matrix

Every number a font stores is in font units — `unitsPerEm` to an em,
1000 in a CFF font and 2048 in most TrueType ones. Outlines come out in
font units, advances come out in font units, and
`fontmetric.scale_for_px` hands back the one `GeomXform` that maps
them. Nothing converts for the caller.

The reason is a cache and a sum. A rasteriser holds one outline per
glyph and draws it at whatever size is asked, so the outline must not
know the size. A shaper accumulates advances across a run and rounds
**once**, because rounding per glyph accumulates into a line that is
visibly the wrong length by the fortieth character. A library that
returned pixels would make both impossible and would look more
convenient doing it. The y axis is flipped in that matrix, because a
font's y grows up from the baseline and an image's grows down.

### Kerning has one source and never two

A font may carry a legacy `kern` table **and** a `GPOS` table with a
`kern` feature, and a great many do — the same pairs in both, one for
software from before 1998 and one for everything since. Applying both
moves the letters twice, and the result is text that is consistently,
subtly too tight: not broken enough to notice, wrong on every line.

`fontkern.kern_source` answers one source, `FontKernPlan` carries which
one it chose, and there is no call that reads both.
`fontkern.has_both_sources` is published so a validator can report the
condition, and `fontread.read_kerning` reads `GPOS` first and touches
`kern` only when `GPOS` has nothing — so the rule saves a read as well
as a mistake.

## What this does not do, by name

| | |
| --- | --- |
| **Complex scripts** | Arabic joins, Devanagari reorders, Thai stacks. Those need joining state, reordering and mark attachment, which is HarfBuzz's subject and `libharfbuzz-sys`'s row on the bindings shelf. `fontshape.shape` **refuses** a run containing one, with `FontComplexScript` carrying the codepoint, rather than laying it out in isolated forms — because bad Arabic is not slightly wrong text, it is unreadable text that looks like text, and a caller would ship it. |
| **Bidirectional text** | The Unicode bidirectional algorithm runs on characters before a font is chosen. It belongs in a `unicode-nv` the grid does not yet have. `fontshape.is_right_to_left` names the property so a caller can route; nothing here reorders. |
| **Hinting** | The TrueType instruction set is a virtual machine whose whole job is moving points at small sizes, and `fontcff`'s hint operators are read and not acted on. Modern rendering is mostly unhinted with vertical-only stem darkening; the gap it leaves is bitmap quality below about 11 pixels per em. |
| **Rasterising** | raster-nv's, which is the sibling row in this lane. This package answers outlines; that one fills them. |
| **`cmap` formats 0, 2, 6, 8, 10, 13 and 14** | Listed by `fontcmap.formats_refused`. Format 14 — variation selectors — is the one a text renderer will eventually want, and it is named rather than left as an omission. |
| **CFF `flex`, `seac` and the arithmetic operators** | Listed by `fontcff.operators_refused`. They are not equal: `flex` is a curve-smoothing pair that shipped fonts do use and whose absence loses a shallow curve, so it is the first thing the implementation adds. The arithmetic and storage group is Type 2 machinery no shipped font uses. |
| **CFF2, and `typ1`** | Refused by name. CFF2's outlines are a function of design axes rather than a shape, and reading one as CFF produces plausible garbage. |
| **Variable fonts** | `fvar`, `gvar`, `avar` and the rest. A variable font's default instance reads correctly through this package; a named instance does not exist until the deltas are applied. Its own row. |
| **Bitmap and colour tables** | `EBDT`, `CBDT`, `sbix`, `COLR`/`CPAL`. An emoji font read here answers outlines where it has them and `.notdef` where its glyphs are pictures. |
| **WOFF and WOFF2** | See below — the second one is waiting on a sibling in this same lane. |

## WOFF2 is waiting on brotli-nv

`orbit/website` serves web fonts, and a web font on the wire is WOFF2:
the same sfnt tables, in a different container, **Brotli-compressed**.
This package reads the container it is handed and does not decompress —
but the two halves it would need are the table directory that is
already here and a Brotli decoder, which is `brotli-nv`, staged as an
interface in this same lane.

So the WOFF2 row is a real one and its dependencies are named: font-nv
for the directory and the tables, brotli-nv for the stream, and the
format's own glyph-record transform, which is the only genuinely new
work. It is not in this package because a font reader that also
decompressed would make every consumer download a compressor to read a
`.ttf` off disk.

## Where the path type belongs

This package depends on **svg-nv**, for `SvgPath` and `SvgPathCmd`.
The plan's note for this row says "geometry-nv path commands", and
geometry-nv has no path type — it stops at `GeomPoly`, a closed list of
points, which cannot hold a curve at all. svg-nv's path is the only
typed path on the grid, it has the `SvgQuadTo` variant TrueType needs
with the control point kept exact, and it is `core` with geometry-nv
under it. So outlines are `SvgPath`.

**That dependency is the wrong shape for the right reason**, and the
finding is worth stating plainly rather than leaving in a manifest
comment: a font reader and a rasteriser should not both be downloading
an XML writer in order to agree on four curve commands. `SvgPath`,
`SvgPathCmd` and `SvgSubpath` describe geometry, not SVG; moving them
into geometry-nv and leaving svg-nv to re-export them is a
one-package change, and this row would take it the day it lands.
Nothing here would change but a `use` line.

Declaring a `FontPath` of our own was the alternative, and it is worse
in a way the grid is specifically arranged to avoid: raster-nv would
then have to accept two path types that mean the same thing, and
`docs/publishing.md` § Public type names are globally unique is about
exactly that failure.

## What it replaces

`orbit/novoterm` builds its glyph atlas today through `std.text`, which
is an `@ffi` trampoline over **FreeType** — `novo_text_load_face`,
`novo_text_render_glyph`, `novo_text_bitmap_pixel`, and a fallback that
draws binary stripes when libfreetype is missing. Its `font.nv` also
re-declares those externs locally, because a package build hides the
standard library from a sibling module.

font-nv plus raster-nv is that path natively: `fontread.read_outlines`
for the 95 ASCII glyphs, `rastergl.fill_glyph` into the atlas image.
What it buys is not speed — FreeType is faster — it is that the
terminal stops needing a C library to draw a character, that the
procedural fallback stops being a thing anyone sees, and that the whole
path builds for wasm.

## The layer, and why

`core`. A font file is bytes somebody else read, and everything this
package does to them is arithmetic: a directory lookup, a binary
search, a quadratic curve, an advance width. Nothing is opened and
nothing is written.

The one place that could have gone the other way is answered with a
trait rather than an effect, which is § The load-bearing interface
above.

**No `@tier(embedded)` claim**, and the absence is deliberate rather
than an oversight. `docs/publishing.md` says a device claim is built
and not asserted, and the honest reading is that there is no real
device consumer: a firmware with a display ships a pre-rasterised
bitmap font, because a TrueType parser plus a rasteriser is tens of
kilobytes to draw text the device already knows the shape of. Several
types here are `@value` and several functions are integer arithmetic,
so a subset would probably link — but a claim nobody needs is a claim
nobody maintains.

## Dependencies

| | |
| --- | --- |
| `geometry-nv ^0.0.1` | `GeomXform` for the composite-glyph matrix and the units-to-pixels transform, `GeomRectF` for bounding boxes. Declaring a second affine matrix here would put two incompatible ones in a program, which `E2004` refuses at the consumer. |
| `svg-nv ^0.0.1` | `SvgPath` and `SvgPathCmd`. See § Where the path type belongs. |

Nothing else. **No unicode-nv**, which the grid does not have: script
identification here is the coarse ranges `fontshape.script_of` needs to
pick an OpenType script tag, and it is not a substitute for character
properties. **No compression package**: see § WOFF2 above.

## The reference implementation

`ttf-parser` (MIT/Apache-2.0) for the surface and the shape — it is the
Rust crate that reads a font without allocating, which is the same
constraint a `core` package has — and `fontTools` for the parts a
reader argues about. FreeType is the behavioural reference: where this
package and FreeType disagree about a glyph, FreeType is right.

The test vectors are the OpenType specification's own worked examples
(the format 4 `cmap`, the `hmtx` rule, the CFF subroutine bias
thresholds) plus `ttf-parser`'s fixture shape — a directory built by
hand in front of the tables it names.

## Status

| | |
| --- | --- |
| version | 0.0.1, `stability = "draft"` |
| modules | 11 |
| public functions | 185, every body a `todo()` |
| public types | 22 boxed structs, 5 `@value` structs, 6 enums with 31 variants, 1 trait |
| tests | 52, 317 assertions, red until bodies land |
| device claim | none, and § The layer says why |
