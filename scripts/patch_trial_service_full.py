
import os

file_path = 'backend/app/services/trial_generation_service.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix resolve_face_reference unpacking in generate_preview_images_inner
old_unpack_1 = '_face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss)'
new_unpack_1 = '_face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss)'

if old_unpack_1 in content:
    content = content.replace(old_unpack_1, new_unpack_1)
    print("Fixed unpack 1")
else:
    print("Unpack 1 not found or already fixed")

# 2. Add original_photo_url to generate_consistent_image in generate_preview_images_inner
# We look for a unique parameter to anchor the replacement
anchor_1 = 'child_face_url=_face_ref_url or "",'
new_param_1 = 'child_face_url=_face_ref_url or "",\n                        original_photo_url=_original_photo_url,'

# Careful, this anchor might appear multiple times. We need to be specific.
# The first occurrence corresponds to generate_preview_images_inner
# But let's try to replace all occurrences if variables match.
# In all 3 functions, the variable name is _original_photo_url (after my fix above) and _face_ref_url.
# So replacing the anchor globally might work if I fix all unpackings first.

# 3. Fix resolve_face_reference unpacking in generate_composed_preview_inner
old_unpack_2 = '_face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_comp)'
new_unpack_2 = '_face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_comp)'

if old_unpack_2 in content:
    content = content.replace(old_unpack_2, new_unpack_2)
    print("Fixed unpack 2")
else:
    print("Unpack 2 not found or already fixed")

# 4. Fix resolve_face_reference unpacking in generate_remaining_images_inner
old_unpack_3 = '_face_ref_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_rem)'
new_unpack_3 = '_face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(child_photo_url, _ss_rem)'

if old_unpack_3 in content:
    content = content.replace(old_unpack_3, new_unpack_3)
    print("Fixed unpack 3")
else:
    print("Unpack 3 not found or already fixed")

# Now replace the function call arguments.
# Since I've introduced _original_photo_url in all 3 scopes, I can safely add it to the call.
if anchor_1 in content:
    content = content.replace(anchor_1, new_param_1)
    print("Added original_photo_url param to calls")
else:
    print("Anchor for param replacement not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
