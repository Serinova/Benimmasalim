import re
import os

filepath = "src/app/create-v2/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace STEP_DEFS
new_steps = """const STEP_DEFS = [
  { label: "Kahraman & Macera", shortLabel: "Kahraman", icon: <Sparkles className="h-4 w-4" /> },
  { label: "Kitabını İncele", shortLabel: "Önizleme", icon: <Eye className="h-4 w-4" /> },
  { label: "Teslimat & Ödeme", shortLabel: "Ödeme", icon: <CreditCard className="h-4 w-4" /> },
  { label: "Tamamlandı", shortLabel: "Tamam", icon: <PartyPopper className="h-4 w-4" /> },
];

type SubStep =
  // Step 1: Kahraman & Macera (Setup)
  | "setup"
  // Step 2: İnceleme & Önizleme & Upsells
  | "reveal"
  // Step 3: Checkout
  | "checkout"
  // Step 4: Success
  | "success";"""

content = re.sub(
    r"const STEP_DEFS = \[.*?type SubStep =[^{]*?;", 
    new_steps, 
    content, 
    flags=re.DOTALL
)

# Update Initial SubStep
content = content.replace(
    """const [subStep, setSubStep] = useState<SubStep>(\n    preselectedScenarioId ? "child-info" : "adventure"\n  );""",
    """const [subStep, setSubStep] = useState<SubStep>("setup");"""
)

# Insert the "Generate & Preview" combined logic
# Currently there is "handleGenerateStory" and "handleGeneratePreview"
# Let's create "handleMagicWand"
magic_logic = """
  // ─── Magic Wand: Story + Preview combined ─────────────────────
  const handleMagicWand = async () => {
    // Basic validation
    if (!childInfo.name || !selectedScenario || !selectedStyle) {
      toast({ title: "Eksik Bilgiler", description: "Lütfen tüm bilgileri ve fotoğraf/stili tamamlayın.", variant: "destructive" });
      return;
    }
    
    // Auto-select a default product format (A4 if empty)
    if (!selectedProduct && products.length > 0) {
       setSelectedProduct(products[0].id);
    }
    
    // Step 1: Generate Story
    setLoading(true);
    let stStructure = storyStructure;
    if (!stStructure) {
        try {
          const stylePrompt = getSelectedStylePrompt();
          const p = buildStoryPayload(
            selectedScenario, childInfo.name, parseInt(childInfo.age) || 7, childInfo.gender, 
            stylePrompt, "tr", {}, "", childInfo.clothingDescription, getSelectedOutcomeNames(), customVariables
          );
          
          let uploadUrl = undefined;
          if (childPhotoPreview && !childPhotoPreview.startsWith("http")) {
            const up = await uploadTempImage(childPhotoPreview);
            if (up.success && up.url) uploadUrl = up.url;
          }
          if (uploadUrl || (childPhotoPreview && childPhotoPreview.startsWith("http"))) {
              p.child_photo_url = uploadUrl || childPhotoPreview;
          }

          const data = await generateStoryV2(p);
          if (data.success && data.story) {
            setStoryStructure({ title: data.story.title || "Adsız Hikaye", pages: data.story.pages });
            setStoryMetadata({ clothing_description: data.story.clothing_description });
            stStructure = { title: data.story.title || "Adsız Hikaye", pages: data.story.pages };
          } else {
             throw new Error("Hikaye oluşturulamadı");
          }
        } catch (e) {
          toast({ title: "Hata", description: "Hikaye hatası.", variant: "destructive" });
          setLoading(false); return;
        }
    }
    
    // Step 2: Generate Preview
    setPreviewLoading(true);
    try {
      let childPhotoUrl: string | null = null;
      if (childPhotoPreview && !childPhotoPreview.startsWith("http")) {
         const up = await uploadTempImage(childPhotoPreview);
         if (up.success && up.url) childPhotoUrl = up.url;
      } else if (childPhotoPreview) {
         childPhotoUrl = childPhotoPreview;
      }
      
      const selectedStyleObj = visualStyles.find((s) => s.id === selectedStyle);
      const data = await generatePreviewImages({
        user_id: leadUserId || parentInfo?.userId || null,
        parent_name: "Kullanıcı", 
        parent_email: "geçici@benimmasalim.com",
        parent_phone: "",
        child_name: childInfo.name,
        child_age: Number.parseInt(childInfo.age) || 7,
        child_gender: childInfo.gender,
        child_photo_url: childPhotoUrl,
        product_id: selectedProduct || products[0]?.id || null,
        product_name: "A4",
        product_price: 350,
        story_title: stStructure.title,
        story_pages: stStructure.pages.map((p) => ({
          page_number: p.page_number, text: p.text, visual_prompt: p.visual_prompt,
          ...(p.v3_composed ? { v3_composed: true, negative_prompt: p.negative_prompt || "" } : {}),
          ...(p.page_type ? { page_type: p.page_type } : {}),
          ...(p.composer_version ? { composer_version: p.composer_version } : {}),
          ...(p.pipeline_version ? { pipeline_version: p.pipeline_version } : {}),
        })),
        scenario_id: selectedScenario || null,
        scenario_name: scenarios.find((s) => s.id === selectedScenario)?.name || null,
        visual_style: getSelectedStylePrompt(),
        visual_style_name: selectedStyleObj?.name || null,
        clothing_description: normalizeClothingDescription(storyMetadata?.clothing_description || childInfo.clothingDescription) || undefined,
        id_weight: selectedStyleObj?.id_weight || null,
      });

      if (data.success && data.trial_id) {
        setTrialId(data.trial_id);
        setTrialToken(data.trial_token ?? null);
        await pollPreviewStatus(data.trial_id, data.trial_token ?? undefined);
        goToMainStep(2, "reveal"); // Move to Step 2 (Reveal) instantly
      } else {
         throw new Error("Önizleme başlatılamadı.");
      }
    } catch (e) {
       toast({ title: "Hata", description: "Önizleme başlatılamadı.", variant: "destructive" });
    } finally {
       setLoading(false);
    }
  };
"""

content = content.replace("  // ─── Render helpers", magic_logic + "\n  // ─── Render helpers")

# Replace navigation mapping
content = content.replace(
"""                const firstSubs: Record<number, SubStep> = {
                  1: "child-info",
                  2: "product",
                  3: "story-review",
                  4: "checkout",
                  5: "success",
                };""",
"""                const firstSubs: Record<number, SubStep> = {
                  1: "setup",
                  2: "reveal",
                  3: "checkout",
                  4: "success",
                };""")


# Now the hardest part, the JSX `main` tag rendering. This is too large. 
# We'll use a regex replacement or slicing.
main_jsx = """
      <main className="mx-auto w-full min-w-0 max-w-6xl px-3 py-4 sm:px-4">
        <div className="grid min-w-0 gap-4 lg:grid-cols-3">
          {/* Main content area */}
          <div className="min-w-0 lg:col-span-2">
            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 1: Kahramanını Yarat (Setup)                            */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 1 && subStep === "setup" && (
              <div className="space-y-8 pb-20 sm:pb-6">
                
                {/* 1. Header */}
                <div className="text-center">
                  <h1 className="text-xl font-bold text-gray-800">
                    <Sparkles className="mr-1.5 inline h-5 w-5 text-purple-500" />
                    Hikayenin Temelleri
                  </h1>
                </div>

                {/* 2. Çocuk Bilgileri */}
                <Card className="border-0 shadow-sm">
                  <CardContent className="p-4 sm:p-6">
                    <h2 className="mb-4 text-lg font-bold text-gray-800">1. Çocuğun Bilgileri</h2>
                    <ChildInfoForm
                      childInfo={childInfo}
                      onUpdate={setChildInfo}
                      onContinue={() => {}}
                      onBack={() => {}}
                      hideNavButtons
                      hideClothing
                    />
                  </CardContent>
                </Card>

                {/* 3. Macera & Senaryo Seçimi */}
                <Card className="border-0 shadow-sm">
                  <CardContent className="p-4 sm:p-6">
                    <h2 className="mb-4 text-lg font-bold text-gray-800">2. Senaryo Seçimi</h2>
                    <AdventureSelector
                      scenarios={scenarios}
                      selectedScenario={selectedScenario}
                      onSelect={(id) => setSelectedScenario(id)}
                      onContinue={() => {}}
                      onBack={() => {}}
                      hideNavButtons
                    />
                  </CardContent>
                </Card>
                
                {/* 4. Stil & Fotoğraf Seçimi */}
                <Card className="border-0 shadow-sm">
                  <CardContent className="p-4 sm:p-6">
                    <h2 className="mb-4 text-lg font-bold text-gray-800">3. Vizyon ve Karakter (Fotoğraf)</h2>
                    <PhotoUploaderStep
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
                    />
                    
                    <div className="mt-8 border-t pt-8">
                       <h2 className="mb-4 text-lg font-bold text-gray-800">4. Görsel Çizim Stili</h2>
                       <StyleSelectorStep
                         visualStyles={visualStyles}
                         selectedStyle={selectedStyle}
                         onSelect={(id, _w) => { setSelectedStyle(id); setCustomIdWeight(_w || null); }}
                         onContinue={() => {}}
                         onBack={() => {}}
                         hideNavButtons
                       />
                    </div>
                  </CardContent>
                </Card>

                <div className="sticky bottom-0 z-10 w-full pt-4 pb-4">
                  <Button
                    size="lg"
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-lg font-bold h-14"
                    onClick={handleMagicWand}
                    disabled={loading || uploadingPhoto}
                  >
                    {loading ? "Sihir Yapılıyor... Lütfen Bekleyin 🪄" : "Masalımı Oluştur! 🪄"}
                  </Button>
                </div>
              </div>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 2: Kitabını İncele & Önizleme & Upsells (Reveal)        */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 2 && subStep === "reveal" && storyStructure && (
               <div className="space-y-6 pb-20 sm:pb-6">
                   <div className="text-center">
                      <h1 className="text-xl font-bold text-gray-800 mb-2">
                        🎉 Kitabın Hazır!
                      </h1>
                      <p className="text-gray-600">
                        {childInfo.name} başrolde olduğu {storyStructure.title} ortaya çıktı.
                      </p>
                   </div>
                   
                   <ImagePreviewStep
                    childName={childInfo.name}
                    previewImages={previewImages}
                    backCoverImageUrl={previewImages["backcover"] ?? null}
                    onApprove={() => goToMainStep(3, "checkout")}
                    onBack={() => goToMainStep(1, "setup")}
                    isLoading={previewLoading}
                    generationProgress={generationProgress}
                    storyPages={storyStructure.pages}
                    hideStoryTexts={false}
                   />
                   
                   {/* Upsell Audio & Extras (Embedded below preview) */}
                   <Card className="mt-6 border-purple-200 bg-purple-50/50">
                       <CardContent className="p-4">
                           <h3 className="font-bold text-lg mb-2 text-purple-800">Sihirli Eklentiler 🪄</h3>
                           <AudioSelectionStep
                            childName={childInfo.name}
                            basePrice={calculateTotalPrice()}
                            selectedOption={!hasAudioBook ? "none" : audioType}
                            systemVoice={systemVoice}
                            clonedVoiceId={clonedVoiceId}
                            isCloningVoice={isCloningVoice}
                            onOptionChange={(opt) => {
                              if (opt === "none") setHasAudioBook(false);
                              else { setHasAudioBook(true); setAudioType(opt); }
                            }}
                            onSystemVoiceChange={setSystemVoice}
                            onVoiceRecorded={handleVoiceSampleRecorded}
                            onContinue={() => goToMainStep(3, "checkout")}
                            onBack={() => {}}
                            isTestMode={false}
                            isSubmitting={false}
                            hideNavButtons
                           />
                           
                           {/* Coloring Book Added Manually Here */}
                           <div className="mt-4 p-4 rounded-xl border border-pink-200 bg-white">
                                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                                  <div>
                                    <h4 className="font-bold text-gray-800 text-md">🖍️ Çizim & Boyama Kitabı Ekle</h4>
                                    <p className="text-sm text-gray-600">AI ile çocuklara uygun siyah beyaz sayfalar</p>
                                  </div>
                                  <Button 
                                    variant={hasColoringBook ? "destructive" : "default"}
                                    onClick={() => setHasColoringBook(!hasColoringBook)}
                                  >
                                    {hasColoringBook ? "Kaldır" : "+ Ekle (" + coloringBookPrice + "₺)"}
                                  </Button>
                                </div>
                           </div>
                       </CardContent>
                   </Card>
                   
                   <div className="sticky bottom-0 z-10 w-full pt-4 pb-4">
                      <Button
                        size="lg"
                        className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-lg font-bold h-14"
                        onClick={() => goToMainStep(3, "checkout")}
                      >
                        Sepeti Onayla ➔
                      </Button>
                    </div>
               </div>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 3: Teslimat & Ödeme (Checkout)                        */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 3 && subStep === "checkout" && storyStructure && (
              <CheckoutStep
                childName={childInfo.name}
                storyTitle={storyStructure.title}
                coverImageUrl={Object.values(previewImages).length > 0 ? Object.values(previewImages)[0] : ""}
                onBack={() => goToMainStep(2, "reveal")}
                onSubmitOrder={(testParentInfo, note, promoCode, hasColParam) => {
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
                }}
              />
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* STEP 4: Success                                            */}
            {/* ════════════════════════════════════════════════════════════ */}
            {mainStep === 4 && subStep === "success" && (
                <div className="rounded-2xl border border-green-100 bg-white p-6 sm:p-10 text-center shadow-xl">
                 <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-green-100">
                   <PartyPopper className="h-12 w-12 text-green-600" />
                 </div>
                 <h2 className="mb-4 text-2xl font-bold text-gray-800">Siparişiniz Başarıyla Alındı!</h2>
                 <p className="mb-8 text-gray-600">
                   Masal diyarındaki serüven başlıyor! Hazırlık aşamalarını e-posta üzerinden takip edebilirsiniz.
                 </p>
                 <Button onClick={() => window.location.href = "/"} size="lg" className="px-8">
                   Ana Sayfaya Dön
                 </Button>
               </div>
            )}

          </div>

          {/* Right sidebar: Summary panel */}
           <div className="hidden lg:block">
            <div className="sticky top-24 pt-10">
              <OrderSummaryPanel
                storyTitle={storyStructure?.title || "Adsız Hikaye"}
                childName={childInfo.name || "Kullanıcı"}
                basePrice={basePrice}
                hasAudioBook={hasAudioBook}
                audioAddonPrice={audioAddonPrice}
                hasColoringBook={hasColoringBook}
                coloringBookPrice={coloringBookPrice}
                totalPrice={calculateTotalPrice()}
                selectedProductName={selectedProductObj?.name}
                productThumbnail={selectedProductObj?.thumbnail_url}
              />
              <div className="mt-4">{renderTrustBar()}</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
"""

# Replace the HTML <main> contents up to </main>
match = re.search(r"<main .*?</main>", content, re.DOTALL)
if match:
    # Just to be safe, find `<main className="mx-auto w-full min-w-0 max-w-6xl px-3 py-4 sm:px-4">`
    # and replace everything until `      </main>` 
    # Because of nested divs, regex might fail. Let's use string split.
    start_str = '      <main className="mx-auto w-full min-w-0 max-w-6xl px-3 py-4 sm:px-4">'
    end_str = '      </main>'
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str) + len(end_str)
    
    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + main_jsx.strip() + content[end_idx:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully injected V2 layout into {filepath}")
