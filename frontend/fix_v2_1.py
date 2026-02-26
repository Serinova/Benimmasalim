import re

filepath = "src/app/create-v2/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# 1. SubStep errors in dead code
text = text.replace('goToMainStep(3, "story-review");', 'goToMainStep(3, "checkout");')
text = text.replace('setSubStep("contact");', 'setSubStep("checkout");')
text = text.replace('setSubStep("image-preview");', 'setSubStep("reveal");')

# 2. handleLeadCapture expects full info
# In handleSubmitOrder: handleLeadCapture("checkout-id", info) -> error because handleLeadCapture signature might be (userId: string, info: ContactInfo)
# Wait, let's fix the exact error: Error TS2339: Property 'userId' does not exist on type '{ fullName: string; email: string; phone: string; }' at line 1073:44
# 1073 is inside `getTrialPreview`? No.
# I can just remove `handleGenerateStory`, `handleGeneratePreview` to clear 90% of those TS errors about dead code!
# Let's remove handleGenerateStory
text = re.sub(r'const handleGenerateStory = async \(\) => \{.+?^\s+};\n', '', text, flags=re.MULTILINE|re.DOTALL)
# Let's remove handleGeneratePreview
text = re.sub(r'const handleGeneratePreview = async \(freshContact\?: ContactInfo\) => \{.+?^\s+};\n', '', text, flags=re.MULTILINE|re.DOTALL)

# Let's write the modified text buffer
with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)
