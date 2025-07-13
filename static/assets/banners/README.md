# Banner Image Instructions

## Getting a Realistic Banner Image

To replace the current gradient banner with a realistic photo of dogs and cats playing in a field with collars and QR code tags, follow these steps:

### Option 1: Stock Photo Websites (Recommended)
1. **Unsplash.com** (Free)
   - Search for: "dogs cats playing field"
   - Look for high-resolution images (at least 1920x400px)
   - Download and save as `hero-banner.jpg`

2. **Pexels.com** (Free)
   - Search for: "pets playing outdoor" or "dogs cats together"
   - Download high-resolution image

3. **Shutterstock.com** (Paid)
   - Search for: "pets with collars playing field"
   - More specific results available

### Option 2: AI Image Generation
Use these prompts with AI image generators:

**DALL-E/Midjourney/Stable Diffusion Prompt:**
```
"Realistic photograph of happy dogs and cats playing together in a beautiful green field, wearing colorful collars with visible dog tags, some tags showing QR codes, others showing a small logo, sunny day, professional photography, high resolution, 16:9 aspect ratio"
```

**Alternative Prompt:**
```
"Professional outdoor photography of various dogs and cats playing in a grassy field, each wearing collars with detailed dog tags, half the tags display QR codes, the other half show a small company logo, natural lighting, realistic photo quality"
```

### Image Requirements:
- **Resolution**: 1920x400px (minimum)
- **Format**: JPG or PNG
- **File size**: Under 2MB for web optimization
- **Aspect ratio**: 16:4 or 4:1 (wide banner format)

### How to Add the Image:
1. Save your image as `hero-banner.jpg`
2. Place it in: `/static/assets/hero-banner.jpg`
3. The CSS is already configured to use this file

### Current Setup:
- The banner CSS is configured in `/static/css/banner.css`
- It will automatically use `/static/assets/hero-banner.jpg` when available
- Falls back to a gradient if the image is not found
- Responsive design included for mobile devices

### Photo Editing Tips:
If you want to add QR codes and logos to an existing photo:
1. Use photo editing software (Photoshop, GIMP, Canva)
2. Add small QR code graphics to some pet tags
3. Add your logo to other pet tags
4. Keep modifications subtle and realistic
5. Ensure the text overlay remains readable

### Example Search Terms:
- "golden retriever labrador playing field"
- "dogs cats together outdoor park"
- "pets with collars sunny day"
- "multiple pets playing grass field"
- "happy pets outdoor portrait"

Once you have your image, simply replace the placeholder and the banner will automatically display your realistic photo!
