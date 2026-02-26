import re

def add_prop(filepath, prop="hideNavButtons?: boolean;"):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Simple regex to insert prop into the first interface definition that ends with Props
    # Example: interface ChildInfoFormProps {
    if "interface " in text and "Props {" in text:
        text = re.sub(r'(interface \w+Props \{)', r'\1\n  ' + prop, text, count=1)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

components = [
    "src/components/ChildInfoForm.tsx",
    "src/components/AdventureSelector.tsx",
    "src/components/PhotoUploaderStep.tsx",
    "src/components/StyleSelectorStep.tsx",
    "src/components/AudioSelectionStep.tsx"
]

for c in components:
    add_prop(c)

# Fix PhotoUploaderStep file prop error: we used `file` instead of `childPhoto` ? Let's check what it expects
# In error 12: src/app/create-v2/page.tsx(1214,23): error TS2322: Type '{ file: ... }' is not assignable to type 'IntrinsicAttributes & PhotoUploaderStepProps'. Property 'file' does not exist...
# It actually expects `childName` and `photoPreview`! Wait, does it expect `childPhoto`? No, it expects `onPhotoSelect` which takes a `file: File`.
# Let's read PhotoUploaderStepProps from page 1210:
# PhotoUploaderStep has: childName, photoPreview, additionalPhotos, onPhotoSelect, onAdditionalPhotoSelect, onRemoveAdditionalPhoto, onAnalyze, isAnalyzing, faceDetected, onContinue, onBack, onClear, parentEmail
# I passed `file={childPhoto}` which is wrong, it doesn't take `file`.
# So we need to remove `file={childPhoto}`, `onFileSelect={...}`, `onPreviewSet={...}`, `uploading={...}`, `setUploading={...}`, `setFaceDetected={...}`, `isRegenerating={...}`, `onAnalyzePhoto={...}`, `childGender={...}` from src/app/create-v2/page.tsx!

filepath = "src/app/create-v2/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# Fix PhotoUploaderStep usage
old_photo_usage = """                    <PhotoUploaderStep
                      file={childPhoto}
                      preview={childPhotoPreview}
                      onFileSelect={(file) => setChildPhoto(file)}
                      onPreviewSet={(p) => setChildPhotoPreview(p)}
                      uploading={uploadingPhoto}
                      setUploading={setUploadingPhoto}
                      faceDetected={faceDetected}
                      setFaceDetected={setFaceDetected}
                      isRegenerating={false}
                      onAnalyzePhoto={handleAnalyzePhoto}
                      onContinue={() => {}}
                      onBack={() => {}}
                      childGender={childInfo.gender}
                      hideNavButtons
                    />"""

new_photo_usage = """                    <PhotoUploaderStep
                      childName={childInfo.name}
                      photoPreview={childPhotoPreview}
                      additionalPhotos={additionalPhotos}
                      onPhotoSelect={(file) => {
                        setChildPhoto(file);
                        setFaceDetected(false);
                        const reader = new FileReader();
                        reader.onload = (e) => setChildPhotoPreview(e.target?.result as string);
                        reader.readAsDataURL(file);
                      }}
                      onAnalyze={handleAnalyzePhoto}
                      isAnalyzing={uploadingPhoto}
                      faceDetected={faceDetected}
                      onContinue={() => {}}
                      onBack={() => {}}
                      onClear={() => {
                        setChildPhoto(null);
                        setChildPhotoPreview("");
                        setFaceDetected(false);
                      }}
                      hideNavButtons
                    />"""

text = text.replace(old_photo_usage, new_photo_usage)

# Fix StyleSelectorStep `onSelect={(id, _w) => ...}` -> `onSelect={(id) => ...}`
old_style_usage = """                       <StyleSelectorStep
                         visualStyles={visualStyles}
                         selectedStyle={selectedStyle}
                         onSelect={(id, _w) => { setSelectedStyle(id); setCustomIdWeight(_w || null); }}
                         onContinue={() => {}}
                         onBack={() => {}}
                         hideNavButtons
                       />"""

new_style_usage = """                       <StyleSelectorStep
                         visualStyles={visualStyles}
                         selectedStyle={selectedStyle}
                         onSelect={(id) => { setSelectedStyle(id); setCustomIdWeight(null); }}
                         onContinue={() => {}}
                         onBack={() => {}}
                         childName={childInfo.name}
                         customIdWeight={customIdWeight}
                         onIdWeightChange={setCustomIdWeight}
                         isLoading={false}
                         hideNavButtons
                       />"""

text = text.replace(old_style_usage, new_style_usage)

# Fix ImagePreviewStep `storyPages` does not exist
# Wait, actually ImagePreviewStep takes: childName, previewImages, backCoverImageUrl, onApprove, onBack, isLoading, generationProgress
# We passed `storyPages` and `hideStoryTexts` which don't exist in ImagePreviewStepProps
old_ip = """                    storyPages={storyStructure.pages}
                    hideStoryTexts={false}"""
text = text.replace(old_ip, "")

# Fix CheckoutStep `onSubmitOrder={...}` -> `onComplete={...}`
# CheckoutStep takes: childName, storyTitle, coverImageUrl, basePrice, audioPrice, hasAudioBook, audioType, productName, coloringBookPrice, initialShipping, onComplete, onBack, isProcessing
old_co = """                onSubmitOrder={(testParentInfo, note, promoCode, hasColParam) => {
                  handleSubmitOrder(testParentInfo, note, promoCode, hasColParam);
                }}
                isSubmitting={submittingOrder}
                productDetails={selectedProductObj ? {
                  name: selectedProductObj.name,
                  description: selectedProductObj.description ?? "",
                  price: basePrice,
                } : undefined}
                extraPagesCount={Math.max(0, storyStructure.pages.length - (selectedProductObj?.default_page_count || 12))}
                extraPagePrice={selectedProductObj?.extra_page_price || 0}
                totalPrice={calculateTotalPrice()}
                trialId={trialId}
                hasAudioBook={hasAudioBook}
                audioBookPrice={audioAddonPrice}
                hasColoringBook={hasColoringBook}
                coloringBookPrice={coloringBookPrice}
                contactInfo={contactInfo}
                onContactUpdate={(info) => {
                    handleLeadCapture("checkout-id", info);
                }}"""

new_co = """                coverImageUrl={Object.values(previewImages).length > 0 ? Object.values(previewImages)[0] : ""}
                basePrice={basePrice}
                audioPrice={audioAddonPrice}
                hasAudioBook={hasAudioBook}
                audioType={audioType}
                productName={selectedProductObj?.name || "Kişisel Hikaye Kitabı"}
                coloringBookPrice={coloringBookPrice}
                initialShipping={contactInfo ? { fullName: `${contactInfo.firstName} ${contactInfo.lastName}`.trim(), email: contactInfo.email || "", phone: contactInfo.phone || "" } : undefined}
                onComplete={(shippingInfo, _paymentInfo, promoCode, hasColoringBookParam) => {
                  const pi = { fullName: shippingInfo.fullName, email: shippingInfo.email, phone: shippingInfo.phone };
                  setParentInfo(pi);
                  setDedicationNote(shippingInfo.dedicationNote || "");
                  setHasColoringBook(hasColoringBookParam || false);
                  handleSubmitOrder(pi, shippingInfo.dedicationNote || "", promoCode ?? undefined, hasColoringBookParam);
                }}
                isProcessing={submittingOrder}"""

# A bit risky to regex replace the huge block, but we can do it by finding 'onSubmitOrder' and replacing up to '/>' 
import re
text = re.sub(r'onSubmitOrder=\{\(testParentInfo.*?\} \/>', new_co + '\n              />', text, flags=re.DOTALL)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)
