# oracle.py - the shaping and outline answers of HarfBuzz and FreeType for one
# font, printed in the format tests/oracle/probe.nv prints, so the two outputs
# can be compared line by line.
#
# usage: python3 oracle.py FONT FACE_INDEX TEXT none|liga
#
# HarfBuzz runs with `kern` always on, `liga` on or off as asked, and the
# features this package does not apply (calt, ccmp, clig, locl, rlig, rclt,
# mark, mkmk, curs) off.  FreeType loads each glyph unscaled and unhinted and
# reports the control box of its outline.
import ctypes, sys, struct
from ctypes import c_void_p, c_char_p, c_uint, c_int, c_uint32, c_int32, POINTER, Structure, byref, c_long, c_short, c_ubyte, c_char

hb = ctypes.CDLL('libharfbuzz.so.0')
ft = ctypes.CDLL('libfreetype.so.6')

class HBFeature(Structure):
    _fields_ = [('tag', c_uint32), ('value', c_uint32), ('start', c_uint), ('end', c_uint)]
class HBInfo(Structure):
    _fields_ = [('codepoint', c_uint32), ('mask', c_uint32), ('cluster', c_uint32), ('v1', c_uint32), ('v2', c_uint32)]
class HBPos(Structure):
    _fields_ = [('x_advance', c_int32), ('y_advance', c_int32), ('x_offset', c_int32), ('y_offset', c_int32), ('v', c_uint32)]

hb.hb_blob_create_from_file.restype = c_void_p
hb.hb_blob_create_from_file.argtypes = [c_char_p]
hb.hb_face_create.restype = c_void_p
hb.hb_face_create.argtypes = [c_void_p, c_uint]
hb.hb_font_create.restype = c_void_p
hb.hb_font_create.argtypes = [c_void_p]
hb.hb_buffer_create.restype = c_void_p
hb.hb_buffer_add_utf8.argtypes = [c_void_p, c_char_p, c_int, c_uint, c_int]
hb.hb_buffer_guess_segment_properties.argtypes = [c_void_p]
hb.hb_buffer_set_script.argtypes = [c_void_p, c_uint32]
hb.hb_buffer_set_direction.argtypes = [c_void_p, c_uint]
hb.hb_shape.argtypes = [c_void_p, c_void_p, POINTER(HBFeature), c_uint]
hb.hb_buffer_get_glyph_infos.restype = POINTER(HBInfo)
hb.hb_buffer_get_glyph_infos.argtypes = [c_void_p, POINTER(c_uint)]
hb.hb_buffer_get_glyph_positions.restype = POINTER(HBPos)
hb.hb_buffer_get_glyph_positions.argtypes = [c_void_p, POINTER(c_uint)]
hb.hb_face_get_upem.restype = c_uint
hb.hb_face_get_upem.argtypes = [c_void_p]
hb.hb_feature_from_string.argtypes = [c_char_p, c_int, POINTER(HBFeature)]

def shape(path, face_index, text, liga):
    blob = hb.hb_blob_create_from_file(path.encode())
    face = hb.hb_face_create(blob, face_index)
    font = hb.hb_font_create(face)
    upem = hb.hb_face_get_upem(face)
    buf = hb.hb_buffer_create()
    data = text.encode()
    hb.hb_buffer_add_utf8(buf, data, len(data), 0, len(data))
    hb.hb_buffer_set_direction(buf, 4)  # LTR
    hb.hb_buffer_set_script(buf, struct.unpack('>I', b'Latn')[0])
    feats = []
    for s in ['-calt','-ccmp','-clig','-locl','-rlig','-rclt','-mark','-mkmk','-curs','-liga' if not liga else '+liga','+kern']:
        f = HBFeature(); hb.hb_feature_from_string(s.encode(), -1, byref(f)); feats.append(f)
    arr = (HBFeature * len(feats))(*feats)
    hb.hb_shape(font, buf, arr, len(feats))
    n = c_uint(0)
    infos = hb.hb_buffer_get_glyph_infos(buf, byref(n))
    poss = hb.hb_buffer_get_glyph_positions(buf, byref(n))
    gs = [infos[i].codepoint for i in range(n.value)]
    xs = []; x = 0
    for i in range(n.value):
        xs.append(x + poss[i].x_offset); x += poss[i].x_advance
    return upem, gs, xs, x

# FreeType
class FTVec(Structure): _fields_ = [('x', c_long), ('y', c_long)]
class FTBBox(Structure): _fields_ = [('xMin', c_long), ('yMin', c_long), ('xMax', c_long), ('yMax', c_long)]
ft.FT_Init_FreeType.argtypes = [POINTER(c_void_p)]
ft.FT_New_Face.argtypes = [c_void_p, c_char_p, c_long, POINTER(c_void_p)]
ft.FT_Load_Glyph.argtypes = [c_void_p, c_uint, c_int32]
ft.FT_Outline_Get_CBox.argtypes = [c_void_p, POINTER(FTBBox)]

def outline_boxes(path, face_index, glyphs):
    lib = c_void_p(); ft.FT_Init_FreeType(byref(lib))
    face = c_void_p()
    err = ft.FT_New_Face(lib, path.encode(), face_index, byref(face))
    assert err == 0, err
    res = {}
    # FT_FaceRec: glyph slot pointer at offset; read via ctypes struct prefix
    # FT_FaceRec layout: num_faces,face_index (long,long), face_flags, style_flags, num_glyphs (long x3), family_name, style_name (ptr), num_fixed_sizes(int)+pad, available_sizes(ptr), num_charmaps(int)+pad, charmaps(ptr), generic(ptr,ptr), bbox(4 long), units_per_EM(ushort)... 
    class FaceRec(Structure):
        _fields_ = [('num_faces', c_long), ('face_index', c_long), ('face_flags', c_long), ('style_flags', c_long),
                    ('num_glyphs', c_long), ('family_name', c_void_p), ('style_name', c_void_p),
                    ('num_fixed_sizes', c_int), ('available_sizes', c_void_p), ('num_charmaps', c_int),
                    ('charmaps', c_void_p), ('generic_data', c_void_p), ('generic_fin', c_void_p),
                    ('bbox', FTBBox), ('units_per_EM', ctypes.c_ushort), ('ascender', c_short), ('descender', c_short),
                    ('height', c_short), ('max_advance_width', c_short), ('max_advance_height', c_short),
                    ('underline_position', c_short), ('underline_thickness', c_short), ('glyph', c_void_p)]
    fr = ctypes.cast(face, POINTER(FaceRec)).contents
    class GlyphSlot(Structure):
        _fields_ = [('library', c_void_p), ('face', c_void_p), ('next', c_void_p), ('glyph_index', c_uint), ('generic_d', c_void_p), ('generic_f', c_void_p),
                    ('metrics', c_long * 8), ('linearHoriAdvance', c_long), ('linearVertAdvance', c_long), ('advance', FTVec),
                    ('format', c_uint), ('bitmap', c_ubyte * 40), ('bitmap_left', c_int), ('bitmap_top', c_int)]
    # outline follows: after bitmap_top come FT_Outline
    class Outline(Structure):
        _fields_ = [('n_contours', c_short), ('n_points', c_short), ('points', c_void_p), ('tags', c_void_p), ('contours', c_void_p), ('flags', c_int)]
    for g in glyphs:
        err = ft.FT_Load_Glyph(face, g, 0x2 | 0x8)  # NO_SCALE | NO_HINTING
        if err:
            res[g] = 'ERR %d' % err; continue
        slot = ctypes.cast(fr.glyph, POINTER(GlyphSlot)).contents
        off = GlyphSlot.bitmap_top.offset + 4
        # align to 8
        off = (off + 7) & ~7
        outline_ptr = fr.glyph + off
        ol = ctypes.cast(outline_ptr, POINTER(Outline)).contents
        if ol.n_points == 0:
            res[g] = 'empty'; continue
        bb = FTBBox(); ft.FT_Outline_Get_CBox(outline_ptr, byref(bb))
        res[g] = '%d %d %d %d' % (bb.xMin, bb.yMin, bb.xMax, bb.yMax)
    return res

if __name__ == '__main__':
    path, idx, text, feats = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    upem, gs, xs, w = shape(path, idx, text, feats == 'liga')
    print('UPEM', upem)
    print('GLYPHS', ' '.join(map(str, gs)) + ' ')
    print('XS', ' '.join(map(str, xs)) + ' ')
    print('WIDTH', w)
    seen = []
    for g in gs:
        if g not in seen and len(seen) < 12: seen.append(g)
    boxes = outline_boxes(path, idx, seen)
    for g in seen: print('OUT', g, boxes[g])
