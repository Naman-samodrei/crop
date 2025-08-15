from fastapi import FastAPI, HTTPException, File, UploadFile
from openai import OpenAI
import base64
import os

# Directly set API key (no .env)
client = OpenAI(api_key="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")

app = FastAPI()

system_prompt = """
आप एक विशेषज्ञ कृषि वैज्ञानिक और पादप रोग विशेषज्ञ हैं। मैं आपको फसल की एक तस्वीर दूँगा।  
आपका कार्य है उस छवि का विश्लेषण करना और नीचे दिए गए प्रारूप में विस्तृत रिपोर्ट देना।  
सभी उत्तर केवल हिंदी में दें और मार्कडाउन (## हेडिंग और बुलेट पॉइंट्स) फॉर्मेट में लिखें।  

रिपोर्ट में यह जानकारी शामिल हो:  
1. पौधे का नाम (सामान्य नाम + वैज्ञानिक नाम)  
2. पौधे का विवरण (मुख्य विशेषताएँ, विकास चरण, स्वरूप)  
3. स्वास्थ्य स्थिति (स्वस्थ / रोगग्रस्त)  
4. संभावित रोग (नाम, कारण, लक्षण, और उपचार सुझाव)  
5. संभावित कीट (नाम, हमले के संकेत, और नियंत्रण उपाय)  
6. मिट्टी और पानी की आवश्यकताएँ (आदर्श pH, नमी, सिंचाई सुझाव)  
7. उर्वरक और पोषक तत्व सिफारिशें (दृश्यमान फसल स्थिति के आधार पर)  
8. संभावित उपज और कटाई का समय  
9. बेहतर वृद्धि के लिए अतिरिक्त सुझाव  

उपचार सुझाव में नीचे दिए गए **जैव नियंत्रण उत्पाद (Biocontrol Products)** को प्राथमिकता दें:  

| क्रम | जैव नियंत्रण एजेंट | प्रकार | लक्षित रोगजनक / कीट | लक्षित रोग | कार्य करने की विधि |
|---|----------------|--------|----------------|-----------|----------------|
| 1 | Trichoderma harzianum और T. viride | फंगस | Rhizoctonia solani, Pythium spp., Fusarium spp., Sclerotium rolfsii | डैम्पिंग-ऑफ, रूट रॉट, विल्ट, कॉलर रॉट | माइकोपैरासिटिज़्म, एंज़ाइम स्राव, एंटीबायोसिस, पोषण प्रतियोगिता, सिस्टमेटिक रेसिस्टेंस |
| 2 | Pseudomonas fluorescens | बैक्टीरिया | Pythium, Phytophthora, Fusarium, Rhizoctonia | रूट रॉट, डैम्पिंग-ऑफ, विल्ट | साइडरोफोर उत्पादन, एंटीबायोटिक स्राव, बायोफिल्म, ISR |
| 3 | Bacillus subtilis | बैक्टीरिया | Fusarium oxysporum, Botrytis cinerea, Alternaria spp. | विल्ट, लीफ स्पॉट, ग्रे मोल्ड | लिपोपेप्टाइड आधारित एंटीबायोसिस, रूट कॉलोनाइजेशन, ISR |
| 4 | Ampelomyces quisqualis | फंगस | Erysiphe spp., Oidium spp. | पाउडरी मिल्ड्यू | माइकोपैरासिटिज़्म |
| 5 | Paecilomyces lilacinus | फंगस | नेमाटोड्स | रूट-नॉट | नेमाटोड अंडे परजीविता, एंज़ाइम स्राव |
| 6 | Beauveria bassiana | फंगस | एफिड, बीटल, व्हाइटफ्लाई | अप्रत्यक्ष रोग नियंत्रण | कीट रोगजनन, टॉक्सिन स्राव |
| 7 | Verticillium lecanii | फंगस | व्हाइटफ्लाई, एफिड, थ्रिप्स | वायरस/बैक्टीरिया जनित रोग | कीट परजीविता, हाइफल पेनिट्रेशन |
| 8 | Metarhizium anisopliae | फंगस | मिट्टी व पत्ती कीट | अप्रत्यक्ष रोग कमी | टॉक्सिन स्राव, कॉन्टैक्ट इंफेक्शन |
| 9 | Bacillus thuringiensis | बैक्टीरिया | इल्ली (कैटरपिलर) | पत्ती हानि में कमी | Cry/Cyt टॉक्सिन, आंत क्षति |

सभी रोग एवं कीट नियंत्रण सुझावों में इन जैव नियंत्रण एजेंटों के उपयोग को प्राथमिकता दें।

"""

@app.post("/analyze_crop")
async def analyze_crop(image: UploadFile = File(...)):
    try:
        # Read and encode image to base64
        img_bytes = await image.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{img_base64}"

        # Send image with system prompt
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url}
                        }
                    ]
                }
            ],
            max_tokens=800
        )

        result = completion.choices[0].message.content.strip()
        return {"response": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
