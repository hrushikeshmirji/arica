import { useState, useRef } from "react"
import { Link } from "react-router-dom"
import {
  Camera,
  ShieldCheck,
  Leaf,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Globe,
  Layers,
  Cpu,
  ScanLine,
  BookOpen,
  Smartphone,
  Check,
  Info,
  Image as ImageIcon,
  ChevronRight,
  Sprout,
  LayoutGrid,
} from "lucide-react"
import { useLanguage, Language } from "../contexts/LanguageContext"
import { ThemeToggle } from "../components/ThemeToggle"

interface SpecimenCase {
  id: string
  label: { en: string; kn: string; hi: string }
  name: { en: string; kn: string; hi: string }
  status: { en: string; kn: string; hi: string }
  severity: "critical" | "severe" | "moderate" | "mild" | "healthy"
  image: string
  tagColor: string
  problem: { en: string; kn: string; hi: string }
  treatment: { en: string; kn: string; hi: string }
  organic: { en: string; kn: string; hi: string }
}

const SPECIMEN_CASES: SpecimenCase[] = [
  {
    id: "healthy",
    label: {
      en: "Healthy Leaf",
      kn: "ಆರೋಗ್ಯಕರ ಗರಿ",
      hi: "स्वस्थ पत्ती",
    },
    name: {
      en: "Healthy Arecanut Palm",
      kn: "ಆರೋಗ್ಯಕರ ಮರ",
      hi: "स्वस्थ सुपारी का पेड़",
    },
    status: {
      en: "Healthy — Normal",
      kn: "ಉತ್ತಮ — ಸಾಮಾನ್ಯ",
      hi: "स्वस्थ — सामान्य",
    },
    severity: "healthy",
    image: "/samples/sample_healthy_leaf.jpg",
    tagColor: "bg-emerald-500",
    problem: {
      en: "Vigorous green crown canopy, clear rachis, and well-filled nut clusters with zero pathological necrosis.",
      kn: "ಯಾವುದೇ ರೋಗದ ಲಕ್ಷಣಗಳಿಲ್ಲ. ಗರಿಗಳು ಮತ್ತು ಕಾಯಿಗಳ ಗೊಂಚಲುಗಳು ದೃಢವಾಗಿ ಮತ್ತು ಹಸಿರಾಗಿವೆ.",
      hi: "पेड़ में कोई बीमारी नहीं है। पत्तियां हरी-भरी हैं और फलों के गुच्छे पूरी तरह स्वस्थ हैं।",
    },
    treatment: {
      en: "No fungicides or corrective sprays required. Avoid unnecessary chemical exposure and cost.",
      kn: "ಯಾವುದೇ ಔಷಧಿ ಸಿಂಪಡಣೆ ಅಗತ್ಯವಿಲ್ಲ. ಅನಗತ್ಯ ಕೀಟನಾಶಕಗಳ ವೆಚ್ಚವನ್ನು ತಪ್ಪಿಸಿ.",
      hi: "किसी रासायनिक दवा के छिड़काव की आवश्यकता नहीं है। अनावश्यक कीटनाशक खर्च से बचें।",
    },
    organic: {
      en: "Maintain regular annual nutrition (100g N, 40g P2O5, 140g K2O per palm) and 12-15 kg organic farmyard compost.",
      kn: "ವಾರ್ಷಿಕವಾಗಿ ೧೦-೧೨ ಕೆ.ಜಿ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಮತ್ತು ಶಿಫಾರಸು ಮಾಡಿದ ಪೋಷಕಾಂಶಗಳನ್ನು ನೀಡಿ.",
      hi: "सालाना 10-15 किलो गोबर की सड़ी खाद और संतुलित पोषण प्रबंधन जारी रखें।",
    },
  },
  {
    id: "leaf_spot",
    label: {
      en: "Leaf Spot",
      kn: "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
      hi: "पत्ती धब्बा रोग",
    },
    name: {
      en: "Leaf Spot Disease (Colletotrichum / Phyllosticta)",
      kn: "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
      hi: "पत्ती धब्बा रोग (लीफ स्पॉट)",
    },
    status: {
      en: "Moderate — Active Lesions",
      kn: "ಮಧ್ಯಮ — ಕಲೆಗಳು ಸಕ್ರಿಯ",
      hi: "मध्यम — सक्रिय धब्बे",
    },
    severity: "moderate",
    image: "/samples/sample_leaf_spot.jpg",
    tagColor: "bg-amber-500",
    problem: {
      en: "Circular to irregular yellowish-brown spots with dark brown concentric margins on leaflets, reducing photosynthetic capacity.",
      kn: "ಗರಿಗಳ ಮೇಲೆ ಕಂದು ಬಣ್ಣದ ವೃತ್ತಾಕಾರದ ಚುಕ್ಕೆಗಳು ಕಾಣಿಸಿಕೊಂಡು ಕ್ರಮೇಣ ಒಣಗುತ್ತವೆ.",
      hi: "पत्तियों पर गोलाकार भूरे धब्बे पड़ते हैं जिनके किनारे गहरे होते हैं, जिससे प्रकाश संश्लेषण कम हो जाता है।",
    },
    treatment: {
      en: "Prune severely spotted lower fronds and regulate shade canopy. Apply protective 1% Bordeaux mixture or Copper Oxychloride 50 WP (2.5g/L); unverified systemic triazoles withheld.",
      kn: "ರೋಗಗ್ರಸ್ತ ಕೆಳಗಿನ ಗರಿಗಳನ್ನು ತೆಗೆದು ನೆರಳು ನಿಯಂತ್ರಿಸಿ. ರಕ್ಷಣಾತ್ಮಕ ೧% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಅಥವಾ ಸಿಒಸಿ 50 WP (ಲೀಟರ್‌ಗೆ ೨.೫ ಗ್ರಾಂ) ಸಿಂಪಡಿಸಿ.",
      hi: "अधिक संक्रमित निचली पत्तियों को काटें और छाया नियंत्रित करें। सुरक्षात्मक 1% बोर्डो मिश्रण या कॉपर ऑक्सीक्लोराइड 50 WP (2.5 ग्राम/लीटर) का छिड़काव करें।",
    },
    organic: {
      en: "Spray 5% fermented cow urine or Pseudomonas fluorescens (20g/L) on affected foliage; remove severely spotted lower leaves.",
      kn: "೫% ಗೋಮೂತ್ರ ದ್ರಾವಣ ಅಥವಾ ಸ್ಯೂಡೋಮೊನಾಸ್ (೨೦ ಗ್ರಾಂ) ಸಿಂಪಡಿಸಿ; ಕೆಳಗಿನ ರೋಗಗ್ರಸ್ತ ಗರಿಗಳನ್ನು ತೆಗೆಯಿರಿ.",
      hi: "5% गोमूत्र का अर्क या स्यूडोमोनास (20 ग्राम प्रति लीटर) का छिड़काव करें और पुरानी संक्रमित पत्तियां हटाएं।",
    },
  },
  {
    id: "koleroga",
    label: {
      en: "Koleroga",
      kn: "ಕೊಳೆರೋಗ (ಮಹಾಲಿ)",
      hi: "कोलेरोगा (फल सड़न)",
    },
    name: {
      en: "Fruit Rot (Koleroga / Mahali)",
      kn: "ಕೊಳೆರೋಗ (ಮಹಾಲಿ)",
      hi: "फल सड़न (कोलेरोगा / महाली)",
    },
    status: {
      en: "Critical — Emergency Spray",
      kn: "ಕ್ರಿಟಿಕಲ್ — ತುರ್ತು ಸಿಂಪಡಣೆ",
      hi: "गंभीर — तत्काल छिड़काव",
    },
    severity: "critical",
    image: "/samples/sample_koleroga.jpg",
    tagColor: "bg-orange-600",
    problem: {
      en: "Water-soaked dark lesions appear on developing nuts, causing rot and massive premature fruit shedding during heavy monsoon rains.",
      kn: "ಮುಂಗಾರು ಮಳೆಯ ಸಮಯದಲ್ಲಿ ಕಾಯಿಗಳ ಮೇಲೆ ಕಪ್ಪು ನೀರಿನಂತಹ ಕಲೆಗಳು ಕಾಣಿಸಿಕೊಂಡು ಕಾಯಿಗಳು ಕೊಳೆತು ಉದುರುತ್ತವೆ.",
      hi: "मानसून की बारिश में सुपारी पर काले पानीदार धब्बे पड़ते हैं और कच्चे फल सड़कर समय से पहले गिरने लगते हैं।",
    },
    treatment: {
      en: "Apply prophylactic spray of 1% Bordeaux Mixture or Copper Oxychloride (0.3% / 3g per liter of water) to crown and bunches.",
      kn: "೧% ಬೋರ್ಡೋ ದ್ರಾವಣ ಅಥವಾ ತಾಮ್ರದ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ (ಲೀಟರ್ ನೀರಿಗೆ ೩ ಗ್ರಾಂ) ಗೊಂಚಲು ಮತ್ತು ಸುಳಿಗೆ ಸಿಂಪಡಿಸಿ.",
      hi: "1% बोर्डो मिश्रण या कॉपर ऑक्सीक्लोराइड (3 ग्राम प्रति लीटर पानी) का पत्तियों और गुच्छों पर छिड़काव करें।",
    },
    organic: {
      en: "Collect and deeply bury or burn all fallen infected nuts. Enrich tree basin soil with Trichoderma harzianum bio-fungicide.",
      kn: "ಬಿದ್ದ ರೋಗಗ್ರಸ್ತ ಕಾಯಿಗಳನ್ನು ಸುಟ್ಟು ಹಾಕಿ. ಬುಡಕ್ಕೆ ಟ್ರೈಕೋಡರ್ಮಾ ಸಾವಯವ ಜೈವಿಕ ಶಿಲೀಂಧ್ರನಾಶಕ ಸೇರಿಸಿ.",
      hi: "गिरे हुए संक्रमित फलों को नष्ट करें। पेड़ के आधार पर ट्राइकोडर्मा जैव कवकनाशी का प्रयोग करें।",
    },
  },
  {
    id: "stem_bleeding",
    label: {
      en: "Stem Bleeding",
      kn: "ಕಾಂಡ ಸೋರುವ ರೋಗ",
      hi: "तना रिसाव रोग",
    },
    name: {
      en: "Stem Bleeding (Thielaviopsis paradoxa)",
      kn: "ಕಾಂಡ ಸೋರುವ ರೋಗ",
      hi: "तना रिसाव रोग (स्टेम ब्लीडिंग)",
    },
    status: {
      en: "Critical — Trunk Infection",
      kn: "ಕ್ರಿಟಿಕಲ್ — ಕಾಂಡ ಬಾಧಿತ",
      hi: "गंभीर — तने का संक्रमण",
    },
    severity: "critical",
    image: "/samples/sample_stem_bleeding.jpg",
    tagColor: "bg-red-600",
    problem: {
      en: "Exudation of dark reddish-brown liquid from trunk cracks, spreading upwards; internal fibrous tissue rots and turns black.",
      kn: "ಕಾಂಡದ ಬಿರುಕುಗಳಿಂದ ಕಡು ಕಂದು ಬಣ್ಣದ ದ್ರವ ಸೋರುತ್ತದೆ ಮತ್ತು ಒಳಭಾಗದ ಕಾಂಡ ಕೊಳೆಯಲಾರಂಭಿಸುತ್ತದೆ.",
      hi: "तने की दरारों से गहरे लाल-भूरे रंग का तरल बहता है, जिससे तने के अंदरूनी रेशे सड़ने लगते हैं।",
    },
    treatment: {
      en: "Cleanly chisel decaying bark to healthy wood and burn shavings. Chemical dressings are under agronomic review; obsolete coal tar and banned Tridemorph are prohibited. Consult KVK.",
      kn: "ರೋಗಗ್ರಸ್ತ ಭಾಗವನ್ನು ಶುದ್ಧ ಮರದವರೆಗೆ ಕೆತ್ತಿ ತೆಗೆದು ಸುಟ್ಟು ಹಾಕಿ. ರಾಸಾಯನಿಕ ಲೇಪನಗಳು ಪರಿಶೀಲನೆಯಲ್ಲಿದ್ದು, ಕಲ್ಲಿದ್ದಲು ಟಾರ್ ಮತ್ತು ಟ್ರೈಡೆಮಾರ್ಫ್ ನಿಷೇಧಿಸಲಾಗಿದೆ. ಕೆವಿಕೆ ಸಂಪರ್ಕಿಸಿ.",
      hi: "संक्रमित छाल को स्वस्थ लकड़ी तक छीलकर जला दें। रासायनिक लेप समीक्षाधीन हैं; पुराना कोलतार व प्रतिबंधित ट्राइडेमॉर्फ वर्जित हैं। केवीके से परामर्श लें।",
    },
    organic: {
      en: "Apply neem cake (2kg/tree) and Trichoderma harzianum to the root zone; improve drainage to prevent root waterlogging.",
      kn: "ಬೇರಿನ ಬುಡಕ್ಕೆ ಬೇವಿನ ಹಿಂಡಿ (೨ ಕೆ.ಜಿ) ಮತ್ತು ಟ್ರೈಕೋಡರ್ಮಾ ಸೇರಿಸಿ, ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿದು ಹೋಗಲು ಕಾಲುವೆ ಮಾಡಿ.",
      hi: "पेड़ की जड़ में 2 किलो नीम की खली और ट्राइकोडर्मा डालें तथा जल निकासी का उचित प्रबंध करें।",
    },
  },
  {
    id: "yellow_leaf",
    label: {
      en: "Yellow Leaf",
      kn: "ಹಳದಿ ಎಲೆ ರೋಗ",
      hi: "पीली पत्ती रोग",
    },
    name: {
      en: "Yellow Leaf Disease (Phytoplasma)",
      kn: "ಹಳದಿ ಎಲೆ ರೋಗ (ವೈರಲ್/ಫೈಟೋಪ್ಲಾಸ್ಮಾ)",
      hi: "येलो लीफ डिजीज (पीली पत्ती रोग)",
    },
    status: {
      en: "Severe — Foliar Chlorosis",
      kn: "ತೀವ್ರ — ಗರಿಗಳ ಹಳದಿ",
      hi: "गंभीर — पत्तियों का पीलापन",
    },
    severity: "severe",
    image: "/samples/sample_yellow_leaf.jpg",
    tagColor: "bg-amber-400",
    problem: {
      en: "Characteristic yellowing starting from inner whorl leaflets, spreading outward; crowns become stunted with small black tipped nuts.",
      kn: "ಒಳಭಾಗದ ಎಲೆಗಳಿಂದ ಪ್ರಾರಂಭವಾಗಿ ಗರಿಗಳು ಹಳದಿಯಾಗುತ್ತವೆ, ಕಾಯಿಗಳು ಕಪ್ಪಾಗಿ ಸುಕ್ಕುಗಟ್ಟುತ್ತವೆ.",
      hi: "अंदर की पत्तियों से पीलापन शुरू होकर बाहर फैलता है, पेड़ का विकास रुक जाता है और फल छोटे रह जाते हैं।",
    },
    treatment: {
      en: "Supportive nutrition only (NOT A CURE): Apply balanced NPK + MgSO4 (100g) + ZnSO4 (50g) to sustain palm vigor. Incurable phytoplasma has no chemical cure; fungicides are prohibited.",
      kn: "ಪೋಷಕಾಂಶ ನಿರ್ವಹಣೆ ಮಾತ್ರ (ರೋಗಕ್ಕೆ ಮದ್ದಿಲ್ಲ): ಮರದ ಚೈತನ್ಯ ಕಾಪಾಡಲು NPK + ಮೆಗ್ನೀಸಿಯಮ್ (೧೦೦ ಗ್ರಾಂ) + ಜಿಂಕ್ (೫೦ ಗ್ರಾಂ) ನೀಡಿ. ಫೈಟೋಪ್ಲಾಸ್ಮಾ ರೋಗಕ್ಕೆ ಶಿಲೀಂಧ್ರನಾಶಕ ನಿಷೇಧಿಸಲಾಗಿದೆ.",
      hi: "केवल सहायक पोषण (कोई इलाज नहीं): पेड़ की जीवन शक्ति बनाए रखने के लिए NPK + मैग्नीशियम (100g) + जिंक (50g) दें। फाइटोप्लाज्मा का कोई कवकनाशी इलाज नहीं है।",
    },
    organic: {
      en: "Apply humic acid and micro-nutrient foliar spray with sea-weed extract; irrigate during peak summer months to mitigate moisture stress.",
      kn: "ಹ್ಯೂಮಿಕ್ ಆಮ್ಲ ಮತ್ತು ಸೂಕ್ಷ್ಮ ಪೋಷಕಾಂಶಗಳನ್ನು ನೀಡಿ; ಬೇಸಿಗೆಯಲ್ಲಿ ಸಾಕಷ್ಟು ನೀರು ಒದಗಿಸಿ.",
      hi: "ह्यूमिक एसिड और समुद्री शैवाल अर्क का छिड़काव करें तथा गर्मियों में पर्याप्त सिंचाई सुनिश्चित करें।",
    },
  },
]

export default function Landing() {
  const { language, setLanguage } = useLanguage()
  const [selectedCase, setSelectedCase] = useState<SpecimenCase>(SPECIMEN_CASES[0]) // Default to Healthy Leaf as shown in reference
  const galleryRef = useRef<HTMLDivElement>(null)

  const isIndic = language === "kn" || language === "hi"
  const leadingClass = isIndic ? "leading-relaxed" : "leading-normal"

  const scrollGallery = (direction: "left" | "right") => {
    if (galleryRef.current) {
      const scrollAmount = direction === "left" ? -260 : 260
      galleryRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" })
    }
  }

  // Trilingual UI copy dictionary
  const ui = {
    brandTag: {
      en: "Precision Arecanut Diagnostics",
      kn: "ಅಡಿಕೆ ಬೆಳೆ ರೋಗ ತಪಾಸಣೆ",
      hi: "सटीक सुपारी फसल रोग निदान",
    },
    navHome: { en: "Home", kn: "ಮುಖಪುಟ", hi: "होम" },
    navHow: { en: "How It Works", kn: "ಕಾರ್ಯವೈಖರಿ", hi: "कैसे काम करता है" },
    navExamples: { en: "Examples", kn: "ಮಾದರಿಗಳು", hi: "उदाहरण" },
    navFeatures: { en: "Features", kn: "ವೈಶಿಷ್ಟ್ಯಗಳು", hi: "विशेषताएं" },
    navAbout: { en: "About", kn: "ಕುರಿತು", hi: "के बारे में" },
    heroBadge: {
      en: "AI for Healthier Arecanut Plantations",
      kn: "ಅಡಿಕೆ ತೋಟಗಳ ರಕ್ಷಣೆಗೆ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ",
      hi: "स्वस्थ सुपारी बागानों के लिए AI तकनीक",
    },
    heroH1Line1: {
      en: "SEE THE SIGNS.",
      kn: "ರೋಗದ ಲಕ್ಷಣ ಗುರುತಿಸಿ.",
      hi: "लक्षणों को पहचानें।",
    },
    heroH1Line2: {
      en: "SAVE THE HARVEST.",
      kn: "ನಿಮ್ಮ ಫಸಲನ್ನು ರಕ್ಷಿಸಿ.",
      hi: "अपनी फसल बचाएं।",
    },
    heroSub: {
      en: "ArecaVision AI helps you detect arecanut diseases early using advanced deep learning — from a single field photo.",
      kn: "ಮೊಬೈಲ್ ಕ್ಯಾಮೆರಾದ ಒಂದೇ ಫೋಟೋ ಮೂಲಕ ಅಡಿಕೆ ಮರದ ರೋಗಗಳನ್ನು ಆರಂಭಿಕ ಹಂತದಲ್ಲೇ ಪತ್ತೆಹಚ್ಚಿ ಪರಿಹಾರ ಕಂಡುಕೊಳ್ಳಿ.",
      hi: "मोबाइल से केवल एक फोटो खींचकर उन्नत डीप लर्निंग तकनीक द्वारा सुपारी के रोगों की शुरुआती पहचान करें।",
    },
    primaryCta: {
      en: "Launch AI Detection Studio",
      kn: "ಫೋಟೋ ತಪಾಸಣೆ ಆರಂಭಿಸಿ",
      hi: "AI निदान शुरू करें",
    },
    secondaryCta: {
      en: "Explore Specimen Examples",
      kn: "ರೋಗ ಮಾದರಿಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
      hi: "रोग के नमूने देखें",
    },
    proofEasy: {
      title: { en: "Easy to Use", kn: "ಬಳಸಲು ಸುಲಭ", hi: "उपयोग में आसान" },
      desc: { en: "Just a photo from your field", kn: "ತೋಟದ ಕೇವಲ ಒಂದು ಫೋಟೋ ಸಾಕು", hi: "खेत से सिर्फ एक फोटो" },
    },
    proofMobile: {
      title: { en: "Mobile Friendly", kn: "ಮೊಬೈಲ್ ಸೂಕ್ತ", hi: "मोबाइल अनुकूल" },
      desc: { en: "Works on smartphones", kn: "ಸ್ಮಾರ್ಟ್‌ಫೋನ್‌ನಲ್ಲಿ ಸುಲಭವಾಗಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ", hi: "स्मार्टफ़ोन पर काम करता है" },
    },
    proofAi: {
      title: { en: "AI-Powered", kn: "ಶಕ್ತಿಯುತ AI", hi: "AI-संचालित" },
      desc: { en: "3-stage deep learning pipeline", kn: "೩-ಹಂತದ ನಿಖರ ಡೀಪ್ ಲರ್ನಿಂಗ್", hi: "3-स्तरीय डीप लर्निंग पाइपलाइन" },
    },
    proofGuidance: {
      title: { en: "Actionable Guidance", kn: "ನಿಖರ ಔಷಧ ಸಲಹೆ", hi: "व्यावहारिक मार्गदर्शन" },
      desc: { en: "Understand issues and next steps", kn: "ಸಮಸ್ಯೆ ಮತ್ತು ಪರಿಹಾರದ ವಿವರ", hi: "समस्या और आगे के कदम समझें" },
    },
    previewAnalysisResult: {
      en: "Analysis Result",
      kn: "ವಿಶ್ಲೇಷಣೆ ಫಲಿತಾಂಶ",
      hi: "विश्लेषण परिणाम",
    },
    previewModerate: {
      en: "Moderate",
      kn: "ಮಧ್ಯಮ ತೀವ್ರತೆ",
      hi: "मध्यम",
    },
    previewLeafSpotName: {
      en: "Leaf Spot Disease",
      kn: "ಎಲೆ ಚುಕ್ಕೆ ರೋಗ",
      hi: "पत्ती धब्बा रोग (लीफ स्पॉट)",
    },
    previewLeafSpotDesc: {
      en: "Symptoms of leaf spot detected on arecanut leaf. Early intervention can help prevent further spread.",
      kn: "ಅಡಿಕೆ ಗರಿಯಲ್ಲಿ ಎಲೆ ಚುಕ್ಕೆ ರೋಗದ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿವೆ. ಆರಂಭಿಕ ಸಿಂಪಡಣೆ ರೋಗ ಹರಡುವುದನ್ನು ತಡೆಯುತ್ತದೆ.",
      hi: "सुपारी की पत्ती पर लीफ स्पॉट के लक्षण पाए गए हैं। शुरुआती उपचार से इसे फैलने से रोका जा सकता है।",
    },
    previewViewDetails: { en: "View Details", kn: "ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ", hi: "विवरण देखें" },
    previewManagementTips: { en: "Management Tips", kn: "ಔಷಧ ಮತ್ತು ನಿರ್ವಹಣೆ", hi: "प्रबंधन के सुझाव" },
    previewSimilarCases: { en: "Similar Cases", kn: "ಇತರ ಮಾದರಿಗಳು", hi: "समान मामले" },
    previewDetectedBadge: {
      en: "Detected Disease Regions",
      kn: "ಗುರುತಿಸಲಾದ ರೋಗ ಬಾಧಿತ ಭಾಗ",
      hi: "पहचाने गए रोग प्रभावित क्षेत्र",
    },
    previewIllustrativeLabel: {
      en: "ILLUSTRATIVE PREVIEW",
      kn: "ಮಾದರಿ ಪ್ರದರ್ಶನ (ಡೆಮೋ)",
      hi: "उदाहरणात्मक पूर्वावलोकन (डेमो)",
    },
    previewDemoDataTag: {
      en: "DEMO DATA",
      kn: "ಡೆಮೋ ಮಾಹಿತಿ",
      hi: "डेमो डेटा",
    },
    galleryEyebrow: {
      en: "EXPLORE REAL EXAMPLES",
      kn: "ನೈಜ ರೋಗ ಮಾದರಿಗಳು",
      hi: "वास्तविक रोग के नमूने",
    },
    galleryHeading: {
      en: "Common Arecanut Disease Cases",
      kn: "ಮುಖ್ಯ ಅಡಿಕೆ ರೋಗಗಳ ಮಾದರಿಗಳು",
      hi: "सुपारी के प्रमुख रोग के मामले",
    },
    galleryViewAll: {
      en: "View All Examples",
      kn: "ಎಲ್ಲಾ ಮಾದರಿಗಳು",
      hi: "सभी उदाहरण देखें",
    },
    pipelineEyebrow: {
      en: "HOW ARECAVISION AI WORKS",
      kn: "ಅಡಿಕೆವಿಷನ್ ಕಾರ್ಯವೈಖರಿ",
      hi: "अरेकाविज़न कैसे काम करता है",
    },
    pipelineHeading1: {
      en: "A 3-Stage",
      kn: "೩-ಹಂತದ",
      hi: "3-स्तरीय",
    },
    pipelineHeading2: {
      en: "AI Pipeline for",
      kn: "ನಿಖರ ರೋಗ ಪತ್ತೆ",
      hi: "सटीक निदान के लिए",
    },
    pipelineHeading3: {
      en: "Accurate Detection",
      kn: "ತಂತ್ರಜ್ಞಾನ",
      hi: "AI पाइपलाइन",
    },
    pipelineDesc: {
      en: "We combine three powerful deep learning models to identify arecanut diseases accurately from field photos.",
      kn: "ಕ್ಷೇತ್ರದ ಫೋಟೋಗಳಿಂದ ಅಡಿಕೆ ರೋಗಗಳನ್ನು ನಿಖರವಾಗಿ ಪತ್ತೆಹಚ್ಚಲು ನಾವು ಮೂರು ಅತ್ಯಾಧುನಿಕ AI ಮಾದರಿಗಳನ್ನು ಸಂಯೋಜಿಸುತ್ತೇವೆ.",
      hi: "खेत की तस्वीरों से सुपारी के रोगों की सटीक पहचान के लिए हम तीन शक्तिशाली डीप लर्निंग मॉडलों का संयोजन करते हैं।",
    },
    pipelineLearnMore: {
      en: "Learn More",
      kn: "ಹೆಚ್ಚಿನ ವಿವರ",
      hi: "और जानें",
    },
    stage1Title: { en: "Gatekeeper", kn: "ಗೇಟ್‌ಕೀಪರ್", hi: "गेटकीपर" },
    stage1Model: { en: "EfficientNet-B0", kn: "ಎಫಿಶಿಯೆಂಟ್‌ನೆಟ್-B0", hi: "एफिशिएंटनेट-B0" },
    stage1Desc: {
      en: "Checks if the image contains an arecanut plant and filters out non-arecanut images.",
      kn: "ಚಿತ್ರದಲ್ಲಿ ಅಡಿಕೆ ಮರ ಅಥವಾ ಭಾಗವಿದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸಿ, ಇತರ ಕಳೆ ಗಿಡಗಳನ್ನು ಮೊದಲೇ ತಿರಸ್ಕರಿಸುತ್ತದೆ.",
      hi: "यह जांचता है कि छवि में सुपारी का पौधा है या नहीं और गैर-सुपारी छवियों को बाहर करता है।",
    },
    stage2Title: { en: "Disease Detection", kn: "ರೋಗ ಬಾಧಿತ ಭಾಗ ಪತ್ತೆ", hi: "रोग पहचान" },
    stage2Model: { en: "YOLOv8", kn: "ವೈಓಎಲ್‌ಓ v8", hi: "YOLOv8" },
    stage2Desc: {
      en: "Detects and localizes diseased regions on the leaf or stem.",
      kn: "ಗರಿ ಅಥವಾ ಕಾಂಡದಲ್ಲಿ ರೋಗವಿರುವ ನಿರ್ದಿಷ್ಟ ಸ್ಥಳಗಳನ್ನು ಪತ್ತೆಹಚ್ಚಿ ಗುರುತು ಹಾಕುತ್ತದೆ.",
      hi: "पत्ती या तने पर रोग प्रभावित क्षेत्रों का पता लगाता है और उनका स्थानीयकरण करता है।",
    },
    stage3Title: { en: "Disease Classification", kn: "ರೋಗ ವರ್ಗೀಕರಣ", hi: "रोग वर्गीकरण" },
    stage3Model: { en: "ViT-B/16", kn: "ವಿಷನ್ ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್", hi: "ViT-B/16" },
    stage3Desc: {
      en: "Classifies the detected regions into specific diseases with detailed information.",
      kn: "ಗುರುತಿಸಿದ ಭಾಗಗಳನ್ನು ನಿರ್ದಿಷ್ಟ ರೋಗದ ಹೆಸರಿನೊಂದಿಗೆ ವಿಂಗಡಿಸಿ ಸಂಪೂರ್ಣ ಔಷಧ ಮಾಹಿತಿ ನೀಡುತ್ತದೆ.",
      hi: "पहचाने गए क्षेत्रों को विशिष्ट रोगों में वर्गीकृत करता है और विस्तृत उपचार जानकारी देता है।",
    },
    selectedSymptomLabel: { en: "Clinical Presentation:", kn: "ರೋಗದ ಲಕ್ಷಣಗಳು:", hi: "रोग के लक्षण:" },
    selectedChemicalLabel: { en: "Recommended Spray Protocol:", kn: "ಶಿಫಾರಸು ಮಾಡಿದ ಸಿಂಪಡಣೆ:", hi: "अनुशंसित स्प्रे:" },
    selectedOrganicLabel: { en: "Organic & Cultural Controls:", kn: "ಸಾವಯವ ಮತ್ತು ನೈಸರ್ಗಿಕ ಕ್ರಮ:", hi: "जैविक व प्राकृतिक नियंत्रण:" },
    launchWithSample: {
      en: "Load into Detection Studio →",
      kn: "ಈ ಮಾದರಿಯನ್ನು ತಪಾಸಣಾ ಸ್ಟುಡಿಯೋದಲ್ಲಿ ತೆರೆಯಿರಿ →",
      hi: "इस नमूने को डिटेक्शन स्टूडियो में खोलें →",
    },
    ctaTitle: {
      en: "Inspect Your Arecanut Trees Today.",
      kn: "ಇಂದೇ ನಿಮ್ಮ ಅಡಿಕೆ ಮರಗಳನ್ನು ತಪಾಸಣೆ ಮಾಡಿ.",
      hi: "आज ही अपने सुपारी के पेड़ों की जांच करें।",
    },
    ctaDesc: {
      en: "Capture a field photo with your smartphone to identify disease symptoms, receive ICAR spray dosages, and safeguard your yield.",
      kn: "ಸ್ಮಾರ್ಟ್‌ಫೋನ್ ಮೂಲಕ ಫೋಟೋ ತೆಗೆದು ರೋಗ ಲಕ್ಷಣಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫಸಲನ್ನು ರಕ್ಷಿಸಿ.",
      hi: "स्मार्टफ़ोन से फोटो लेकर तुरंत रोग की पहचान करें, सही दवा की मात्रा जानें और अपनी उपज सुरक्षित रखें।",
    },
  }

  const getSeverityBadge = (severity: SpecimenCase["severity"]) => {
    switch (severity) {
      case "critical":
        return {
          icon: <AlertTriangle size={13} className="text-red-600 dark:text-red-400" aria-hidden="true" />,
          classes: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/50",
        }
      case "severe":
        return {
          icon: <AlertCircle size={13} className="text-orange-600 dark:text-orange-400" aria-hidden="true" />,
          classes: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900/50",
        }
      case "moderate":
        return {
          icon: <AlertCircle size={13} className="text-amber-600 dark:text-amber-400" aria-hidden="true" />,
          classes: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/50",
        }
      case "mild":
        return {
          icon: <Info size={13} className="text-blue-600 dark:text-blue-400" aria-hidden="true" />,
          classes: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900/50",
        }
      case "healthy":
      default:
        return {
          icon: <CheckCircle2 size={13} className="text-emerald-600 dark:text-emerald-400" aria-hidden="true" />,
          classes: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/50",
        }
    }
  }

  const badgeProps = getSeverityBadge(selectedCase.severity)

  return (
    <div className="min-h-screen bg-[#fafaf8] dark:bg-background text-foreground font-sans selection:bg-emerald-600/20 selection:text-foreground">
      {/* ─── 1. TOP NAVIGATION BAR ────────────────────────────────────── */}
      <header className="border-b border-slate-200/80 dark:border-border bg-white/95 dark:bg-card/95 sticky top-0 z-50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
          {/* Brand Logo & Subtitle */}
          <Link
            to="/"
            className="flex items-center gap-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 rounded-lg p-1"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-700 flex items-center justify-center text-white shadow-xs">
              <Leaf size={22} className="stroke-[2.2]" aria-hidden="true" />
            </div>
            <div>
              <span className="font-extrabold text-base sm:text-lg text-slate-900 dark:text-white tracking-tight block leading-tight">
                ArecaVision <span className="text-emerald-700 dark:text-emerald-400">AI</span>
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium hidden sm:block leading-tight">
                {ui.brandTag[language]}
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav aria-label="Main Navigation" className="hidden lg:flex items-center gap-6 xl:gap-8 text-sm font-medium">
            <a
              href="#home"
              className="text-emerald-800 dark:text-emerald-400 font-semibold relative py-1 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-emerald-700 dark:after:bg-emerald-400 after:rounded-full"
            >
              {ui.navHome[language]}
            </a>
            <a
              href="#how-it-works"
              className="text-slate-600 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
            >
              {ui.navHow[language]}
            </a>
            <a
              href="#examples"
              className="text-slate-600 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
            >
              {ui.navExamples[language]}
            </a>
            <a
              href="#features"
              className="text-slate-600 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
            >
              {ui.navFeatures[language]}
            </a>
            <a
              href="#about"
              className="text-slate-600 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
            >
              {ui.navAbout[language]}
            </a>
          </nav>

          {/* Right Header Controls */}
          <div className="flex items-center gap-1.5 sm:gap-3">
            {/* Language Switcher */}
            <div className="flex items-center gap-1 sm:gap-1.5 border border-slate-200 dark:border-border rounded-lg px-2 sm:px-2.5 py-1.5 bg-white dark:bg-card shadow-2xs">
              <Globe size={13} className="text-slate-500 dark:text-slate-400 shrink-0" aria-hidden="true" />
              <label htmlFor="landing-lang-select" className="sr-only">
                Language
              </label>
              <select
                id="landing-lang-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                aria-label="Select language / ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ"
                className="bg-transparent border-none outline-none font-medium text-[11px] sm:text-xs text-slate-800 dark:text-slate-200 cursor-pointer focus-visible:ring-1 focus-visible:ring-emerald-600 rounded-xs"
              >
                <option value="en">English</option>
                <option value="kn">ಕನ್ನಡ</option>
                <option value="hi">हिंदी</option>
              </select>
            </div>

            <ThemeToggle />

            {/* Launch AI Detection Studio Primary Button */}
            <Link
              to="/detection"
              aria-label={ui.primaryCta[language]}
              className="text-xs sm:text-sm font-semibold px-2.5 sm:px-4 py-2 sm:py-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-all flex items-center gap-1.5 sm:gap-2 shadow-xs shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
            >
              <Camera size={16} aria-hidden="true" />
              <span className="hidden sm:inline">{ui.primaryCta[language]}</span>
            </Link>
          </div>
        </div>
      </header>

      {/* ─── 2. HERO SECTION ─────────────────────────────────────────── */}
      <section id="home" className="relative overflow-hidden pt-8 pb-16 lg:pt-14 lg:pb-24 border-b border-slate-200/70 dark:border-border">
        {/* Soft botanical curved background element */}
        <div className="absolute top-10 right-12 w-[520px] h-[520px] rounded-full bg-emerald-100/35 dark:bg-emerald-950/20 blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Content Column (6 cols) */}
            <div className="lg:col-span-6 xl:col-span-6 text-left">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 text-xs font-semibold mb-6">
                <Leaf size={14} className="text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                <span className={leadingClass}>{ui.heroBadge[language]}</span>
              </div>

              {/* Headline */}
              <h1 className={`text-4xl sm:text-5xl lg:text-[3.6rem] font-black tracking-tight leading-[1.08] mb-6 ${leadingClass}`}>
                <span className="block text-slate-900 dark:text-white">{ui.heroH1Line1[language]}</span>
                <span className="block text-emerald-700 dark:text-emerald-400">{ui.heroH1Line2[language]}</span>
              </h1>

              {/* Subheadline Body */}
              <p className={`text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl mb-9 ${leadingClass}`}>
                {ui.heroSub[language]}
              </p>

              {/* Dual CTA Buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 max-w-md sm:max-w-none mb-12">
                <Link
                  to="/detection"
                  className="h-13 px-6 sm:px-7 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-sm flex items-center justify-center gap-2.5 shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
                >
                  <Camera size={18} aria-hidden="true" />
                  <span className={leadingClass}>{ui.primaryCta[language]}</span>
                  <ArrowRight size={16} aria-hidden="true" />
                </Link>

                <a
                  href="#examples"
                  className="h-13 px-6 rounded-xl border border-slate-300 dark:border-border bg-white dark:bg-card hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 font-semibold text-sm flex items-center justify-center gap-2 shadow-2xs transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
                >
                  <ImageIcon size={17} className="text-slate-600 dark:text-slate-300" aria-hidden="true" />
                  <span className={leadingClass}>{ui.secondaryCta[language]}</span>
                </a>
              </div>

              {/* 4 Proof Benefit Indicators */}
              <div className="pt-8 border-t border-slate-200/80 dark:border-border/80 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
                <div>
                  <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-xs sm:text-sm mb-1">
                    <Leaf size={16} className="text-emerald-600 shrink-0" aria-hidden="true" />
                    <span>{ui.proofEasy.title[language]}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                    {ui.proofEasy.desc[language]}
                  </p>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-xs sm:text-sm mb-1">
                    <Smartphone size={16} className="text-emerald-600 shrink-0" aria-hidden="true" />
                    <span>{ui.proofMobile.title[language]}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                    {ui.proofMobile.desc[language]}
                  </p>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-xs sm:text-sm mb-1">
                    <ShieldCheck size={16} className="text-emerald-600 shrink-0" aria-hidden="true" />
                    <span>{ui.proofAi.title[language]}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                    {ui.proofAi.desc[language]}
                  </p>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-xs sm:text-sm mb-1">
                    <Sprout size={16} className="text-emerald-600 shrink-0" aria-hidden="true" />
                    <span>{ui.proofGuidance.title[language]}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                    {ui.proofGuidance.desc[language]}
                  </p>
                </div>
              </div>
            </div>

            {/* Right Visual Composition Column (6 cols) */}
            <div className="lg:col-span-6 xl:col-span-6 relative">
              <div className="relative w-full max-w-lg mx-auto lg:max-w-none">
                {/* Soft circular green halo behind palm tree */}
                <div className="absolute top-4 right-4 w-72 h-72 sm:w-96 sm:h-96 rounded-full bg-emerald-200/50 dark:bg-emerald-900/25 pointer-events-none -z-10" />

                {/* Plantation Canopy Background Image */}
                <div className="relative rounded-3xl overflow-hidden min-h-[470px] sm:min-h-0 aspect-auto sm:aspect-16/11 lg:aspect-4/3 shadow-xl border border-slate-200/80 dark:border-border">
                  <img
                    src="/hero_palm.jpg"
                    alt="Arecanut palm tree with ripe betel nuts in lush plantation"
                    className="w-full h-full object-cover"
                  />
                  {/* Subtle vignette */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/10" />
                </div>

                {/* Floating Diagnostic-Preview Panel (Layered directly over imagery) */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[94%] sm:w-[88%] max-w-[490px] bg-white/98 dark:bg-card/98 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-200/90 dark:border-border p-3.5 sm:p-4 z-20 transition-all hover:shadow-emerald-950/15">
                  <div className="grid grid-cols-12 gap-3 sm:gap-4 items-center">
                    {/* Left Specimen Viewport & Simulated YOLO Box (6 cols) */}
                    <div className="col-span-12 sm:col-span-6">
                      <div className="relative rounded-xl overflow-hidden aspect-4/3 bg-slate-900 border border-slate-200 dark:border-border group">
                        <img
                          src="/samples/sample_leaf_spot.jpg"
                          alt="Leaf Spot Disease Specimen with bounding regions"
                          className="w-full h-full object-cover"
                        />
                        {/* Top Detection Pill Badge */}
                        <div className="absolute top-2 left-2 right-2 z-10 flex items-center justify-between pointer-events-none">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-600/95 text-white text-[10px] font-medium shadow-xs backdrop-blur-xs">
                            <Leaf size={10} />
                            {ui.previewDetectedBadge[language]}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-black/80 text-amber-300 text-[9px] font-mono font-bold tracking-wider uppercase border border-amber-400/40 shadow-xs">
                            {ui.previewDemoDataTag[language]}
                          </span>
                        </div>
                        {/* Simulated YOLO Bounding Box Overlay */}
                        <div className="absolute top-[26%] left-[24%] w-[48%] h-[50%] border-2 border-dashed border-emerald-400 bg-emerald-500/10 rounded-sm pointer-events-none">
                          <span className="absolute -top-4 left-0 bg-emerald-600 text-white text-[9px] font-mono font-bold px-1 rounded-xs">
                            Leaf Spot 92.4% (Simulated)
                          </span>
                        </div>
                        {/* Secondary Lesion Bounding Box */}
                        <div className="absolute top-[52%] left-[28%] w-[26%] h-[28%] border-2 border-red-500 bg-red-500/15 rounded-sm pointer-events-none" />
                        {/* Vertical Thumbnail Strip on Left */}
                        <div className="absolute left-2 bottom-2 top-8 flex flex-col justify-end gap-1 pointer-events-none">
                          <div className="w-5 h-5 rounded-xs overflow-hidden border border-white/80 shadow-xs">
                            <img src="/samples/sample_leaf_spot.jpg" alt="Angle 1" className="w-full h-full object-cover" />
                          </div>
                          <div className="w-5 h-5 rounded-xs overflow-hidden border border-white/80 shadow-xs">
                            <img src="/samples/sample_anthracnose.jpg" alt="Angle 2" className="w-full h-full object-cover" />
                          </div>
                          <div className="w-5 h-5 rounded-xs overflow-hidden border border-white/80 shadow-xs">
                            <img src="/samples/sample_healthy_leaf.jpg" alt="Angle 3" className="w-full h-full object-cover" />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Diagnostic Result Details (6 cols) */}
                    <div className="col-span-12 sm:col-span-6 space-y-2.5 text-left">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                            {ui.previewAnalysisResult[language]}
                          </span>
                          <span className="text-[9px] font-mono uppercase tracking-wider font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 px-1.5 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                            {ui.previewIllustrativeLabel[language]}
                          </span>
                        </div>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800 text-[10px] font-bold shrink-0">
                          <AlertTriangle size={10} />
                          {ui.previewModerate[language]}
                        </span>
                      </div>

                      <div>
                        <h4 className="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white leading-tight">
                          {ui.previewLeafSpotName[language]}
                        </h4>
                        <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed mt-1 line-clamp-2">
                          {ui.previewLeafSpotDesc[language]}
                        </p>
                      </div>

                      {/* Diagnostic Action List */}
                      <div className="space-y-1 pt-1 border-t border-slate-100 dark:border-border/60">
                        <Link
                          to="/detection"
                          className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/80 text-[11px] font-semibold text-slate-700 dark:text-slate-200 transition-colors"
                        >
                          <span className="flex items-center gap-1.5">
                            <Info size={12} className="text-emerald-700 dark:text-emerald-400" />
                            {ui.previewViewDetails[language]}
                          </span>
                          <ChevronRight size={12} className="text-slate-400" />
                        </Link>
                        <a
                          href="#examples"
                          className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/80 text-[11px] font-semibold text-slate-700 dark:text-slate-200 transition-colors"
                        >
                          <span className="flex items-center gap-1.5">
                            <Sprout size={12} className="text-emerald-700 dark:text-emerald-400" />
                            {ui.previewManagementTips[language]}
                          </span>
                          <ChevronRight size={12} className="text-slate-400" />
                        </a>
                        <a
                          href="#examples"
                          className="flex items-center justify-between p-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/80 text-[11px] font-semibold text-slate-700 dark:text-slate-200 transition-colors"
                        >
                          <span className="flex items-center gap-1.5">
                            <Layers size={12} className="text-emerald-700 dark:text-emerald-400" />
                            {ui.previewSimilarCases[language]}
                          </span>
                          <ChevronRight size={12} className="text-slate-400" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Layered Foreground Arecanut Frond (gives rich botanical depth on tablet/desktop) */}
                <div className="absolute -bottom-8 -left-2 sm:-bottom-10 sm:-left-10 lg:-left-12 w-48 sm:w-80 pointer-events-none z-30 select-none hidden sm:block">
                  <img
                    src="/hero_leaf_frond.png"
                    alt=""
                    aria-hidden="true"
                    className="w-full h-auto drop-shadow-2xl"
                  />
                </div>

                {/* Hand-drawn whimsical annotation callouts */}
                <div className="absolute -top-7 right-12 hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 italic pointer-events-none">
                  <span>Healthy Plants, Better Harvests</span>
                  <svg className="w-6 h-6 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M4 14c4-6 10-8 16-2m-4 0l4 2-2-4" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>

                <div className="absolute -bottom-6 left-1/4 hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 italic pointer-events-none z-35">
                  <svg className="w-6 h-6 text-emerald-600 transform -rotate-45" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M4 14c4-6 10-8 16-2m-4 0l4 2-2-4" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>Detect • Identify • Protect • Grow</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 3. COMMON ARECANUT DISEASE CASES (SPECIMEN GALLERY) ──────────── */}
      <section id="examples" className="py-14 sm:py-20 border-b border-slate-200/80 dark:border-border bg-white dark:bg-card scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Gallery Header */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <span className="text-xs font-bold tracking-widest text-slate-500 uppercase block mb-1">
                {ui.galleryEyebrow[language]}
              </span>
              <h2 className={`text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight ${leadingClass}`}>
                {ui.galleryHeading[language]}
              </h2>
            </div>

            {/* Gallery Navigation Buttons */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => scrollGallery("left")}
                  aria-label="Scroll specimens left"
                  className="w-9 h-9 rounded-full border border-slate-200 dark:border-border bg-white dark:bg-card hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors shadow-2xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
                >
                  <ArrowLeft size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => scrollGallery("right")}
                  aria-label="Scroll specimens right"
                  className="w-9 h-9 rounded-full border border-slate-200 dark:border-border bg-white dark:bg-card hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 transition-colors shadow-2xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
                >
                  <ArrowRight size={16} />
                </button>
              </div>

              <Link
                to="/diseases"
                className="text-xs font-semibold px-4 py-2 rounded-lg border border-slate-200 dark:border-border hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 transition-colors flex items-center gap-1.5 shadow-2xs"
              >
                <span>{ui.galleryViewAll[language]}</span>
                <ChevronRight size={14} />
              </Link>
            </div>
          </div>

          {/* Specimen Cards Row */}
          <div
            ref={galleryRef}
            className="flex items-stretch gap-4 sm:gap-6 overflow-x-auto pb-4 pt-1 scrollbar-none snap-x snap-mandatory"
          >
            {SPECIMEN_CASES.map((sc) => {
              const isSelected = sc.id === selectedCase.id
              return (
                <button
                  key={sc.id}
                  type="button"
                  onClick={() => setSelectedCase(sc)}
                  className={`flex-none w-[200px] sm:w-[220px] rounded-2xl overflow-hidden border text-left transition-all cursor-pointer snap-start focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 ${
                    isSelected
                      ? "ring-2 ring-emerald-600 border-emerald-600 bg-emerald-50/20 dark:bg-emerald-950/20 shadow-md transform -translate-y-1"
                      : "border-slate-200 dark:border-border bg-white dark:bg-card hover:border-slate-300 dark:hover:border-slate-700 shadow-2xs"
                  }`}
                >
                  {/* Card Thumbnail Image */}
                  <div className="aspect-4/3 w-full overflow-hidden bg-slate-100 dark:bg-slate-800 relative">
                    <img
                      src={sc.image}
                      alt={sc.label[language]}
                      className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                      loading="lazy"
                    />
                    {isSelected && (
                      <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center shadow-xs">
                        <Check size={12} strokeWidth={3} />
                      </div>
                    )}
                  </div>

                  {/* Card Label */}
                  <div className="p-3.5 flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${sc.tagColor} shrink-0`} />
                    <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white truncate">
                      {sc.label[language]}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>

          {/* Selected Specimen Clinical Presentation Drawer */}
          <div className="mt-8 border border-slate-200 dark:border-border rounded-2xl bg-[#fbfbf9] dark:bg-card/70 p-5 sm:p-7 shadow-xs">
            <div className="grid sm:grid-cols-12 gap-7 items-center">
              {/* Left Photo (4 cols) */}
              <div className="sm:col-span-4">
                <div className="relative aspect-4/3 rounded-xl overflow-hidden border border-slate-200 dark:border-border shadow-xs">
                  <img
                    src={selectedCase.image}
                    alt={selectedCase.name[language]}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-3 left-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold border shadow-2xs ${badgeProps.classes}`}>
                      {badgeProps.icon}
                      <span>{selectedCase.status[language]}</span>
                    </span>
                  </div>
                  <div className="absolute bottom-2.5 left-2.5 text-[10px] bg-black/75 text-white px-2 py-0.5 rounded font-mono">
                    Sample: {selectedCase.id}
                  </div>
                </div>
              </div>

              {/* Right Prescription & Management Protocol (8 cols) */}
              <div className="sm:col-span-8 space-y-4 text-left">
                <div>
                  <h3 className={`text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white ${leadingClass}`}>
                    {selectedCase.name[language]}
                  </h3>
                  <p className={`text-xs sm:text-sm text-slate-600 dark:text-slate-300 mt-1 leading-relaxed ${leadingClass}`}>
                    <strong className="text-slate-800 dark:text-slate-200">{ui.selectedSymptomLabel[language]} </strong>
                    {selectedCase.problem[language]}
                  </p>
                </div>

                <div className="grid sm:grid-cols-2 gap-3.5 pt-2">
                  <div className="p-3.5 rounded-xl border border-emerald-200/80 dark:border-emerald-900/60 bg-emerald-50/60 dark:bg-emerald-950/20">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 dark:text-emerald-300 mb-1">
                      <BookOpen size={14} className="text-emerald-700" />
                      <span>{ui.selectedChemicalLabel[language]}</span>
                    </div>
                    <p className={`text-xs text-slate-700 dark:text-slate-300 leading-relaxed ${leadingClass}`}>
                      {selectedCase.treatment[language]}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl border border-slate-200 dark:border-border bg-white dark:bg-card">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200 mb-1">
                      <Leaf size={14} className="text-emerald-600" />
                      <span>{ui.selectedOrganicLabel[language]}</span>
                    </div>
                    <p className={`text-xs text-slate-600 dark:text-slate-300 leading-relaxed ${leadingClass}`}>
                      {selectedCase.organic[language]}
                    </p>
                  </div>
                </div>

                {/* Direct Action: Load sample into studio */}
                <div className="pt-2">
                  <Link
                    to={`/detection?sample=${selectedCase.id}`}
                    className="inline-flex items-center gap-2 text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
                  >
                    <span>{ui.launchWithSample[language]}</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 4. A 3-STAGE AI PIPELINE FOR ACCURATE DETECTION ─────────────── */}
      <section id="how-it-works" className="py-14 sm:py-20 border-b border-slate-200/80 dark:border-border bg-[#fafaf8] dark:bg-background scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-10 items-center">
            {/* Left Context Column with Botanical Photo (4 cols) */}
            <div className="lg:col-span-4 text-left">
              {/* Botanical image thumbnail */}
              <div className="w-full aspect-16/9 rounded-2xl overflow-hidden mb-6 shadow-sm border border-slate-200/80 dark:border-border">
                <img
                  src="/hero_palm.jpg"
                  alt="Arecanut canopy"
                  className="w-full h-full object-cover"
                />
              </div>

              <span className="text-xs font-bold uppercase tracking-widest text-emerald-700 dark:text-emerald-400 block mb-2">
                {ui.pipelineEyebrow[language]}
              </span>

              <h2 className={`text-3xl sm:text-4xl font-black text-slate-900 dark:text-white tracking-tight leading-[1.12] mb-4 ${leadingClass}`}>
                <span className="text-emerald-700 dark:text-emerald-400">{ui.pipelineHeading1[language]}</span>{" "}
                <span className="block">{ui.pipelineHeading2[language]}</span>
                <span className="block">{ui.pipelineHeading3[language]}</span>
              </h2>

              <p className={`text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-6 ${leadingClass}`}>
                {ui.pipelineDesc[language]}
              </p>

              <div>
                <Link
                  to="/detection"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-300 dark:border-border bg-white dark:bg-card hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 font-semibold text-xs shadow-2xs transition-colors"
                >
                  <span>{ui.pipelineLearnMore[language]}</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            </div>

            {/* Right Connected Pipeline Flow with Arrow Connectors (8 cols) */}
            <div className="lg:col-span-8">
              <div className="grid md:grid-cols-3 gap-4 lg:gap-3 relative items-stretch">
                {/* Stage 1: Gatekeeper */}
                <div className="p-5 sm:p-6 rounded-2xl border border-emerald-200/80 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 shadow-2xs flex flex-col justify-between text-left relative">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-8 h-8 rounded-full bg-emerald-800 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                        1
                      </div>
                      <div className="w-8 h-8 rounded-xl bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 flex items-center justify-center">
                        <Leaf size={16} />
                      </div>
                    </div>

                    <h4 className="font-extrabold text-base text-slate-900 dark:text-white leading-tight">
                      {ui.stage1Title[language]}
                    </h4>
                    <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 block mb-2">
                      {ui.stage1Model[language]}
                    </span>

                    <p className={`text-xs text-slate-600 dark:text-slate-300 leading-relaxed ${leadingClass}`}>
                      {ui.stage1Desc[language]}
                    </p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-emerald-200/60 dark:border-emerald-900/40 text-[11px] text-emerald-800 dark:text-emerald-300 font-medium">
                    Dual Threshold (≥0.74 / &lt;0.52)
                  </div>
                </div>

                {/* Stage 2: Disease Detection */}
                <div className="p-5 sm:p-6 rounded-2xl border border-blue-200/80 dark:border-blue-900/60 bg-blue-50/50 dark:bg-blue-950/20 shadow-2xs flex flex-col justify-between text-left relative">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                        2
                      </div>
                      <div className="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 flex items-center justify-center">
                        <ScanLine size={16} />
                      </div>
                    </div>

                    <h4 className="font-extrabold text-base text-slate-900 dark:text-white leading-tight">
                      {ui.stage2Title[language]}
                    </h4>
                    <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 block mb-2">
                      {ui.stage2Model[language]}
                    </span>

                    <p className={`text-xs text-slate-600 dark:text-slate-300 leading-relaxed ${leadingClass}`}>
                      {ui.stage2Desc[language]}
                    </p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-blue-200/60 dark:border-blue-900/40 text-[11px] text-blue-700 dark:text-blue-300 font-medium">
                    Spatial Lesion Localization
                  </div>
                </div>

                {/* Stage 3: Disease Classification */}
                <div className="p-5 sm:p-6 rounded-2xl border border-amber-200/80 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 shadow-2xs flex flex-col justify-between text-left relative">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                        3
                      </div>
                      <div className="w-8 h-8 rounded-xl bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300 flex items-center justify-center">
                        <Cpu size={16} />
                      </div>
                    </div>

                    <h4 className="font-extrabold text-base text-slate-900 dark:text-white leading-tight">
                      {ui.stage3Title[language]}
                    </h4>
                    <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 block mb-2">
                      {ui.stage3Model[language]}
                    </span>

                    <p className={`text-xs text-slate-600 dark:text-slate-300 leading-relaxed ${leadingClass}`}>
                      {ui.stage3Desc[language]}
                    </p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-amber-200/60 dark:border-amber-900/40 text-[11px] text-amber-800 dark:text-amber-300 font-medium">
                    12-Head Multi-Scale Transformer
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 5. PATHOLOGY CATALOG OVERVIEW ──────────────────────────────── */}
      <section id="features" className="py-14 sm:py-20 border-b border-slate-200/80 dark:border-border bg-white dark:bg-card scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
              Pathology Reference Library
            </span>
            <h2 className={`text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1.5 ${leadingClass}`}>
              {language === "kn"
                ? "ದಕ್ಷಿಣ ಭಾರತದಲ್ಲಿ ಕಂಡುಬರುವ ಮುಖ್ಯ ಅಡಿಕೆ ರೋಗಗಳು"
                : language === "hi"
                ? "दक्षिण भारतीय बागानों में पाए जाने वाले मुख्य सुपारी रोग"
                : "Arecanut Conditions in the Reference Catalog"}
            </h2>
            <p className={`text-xs sm:text-sm text-slate-600 dark:text-slate-300 mt-2 ${leadingClass}`}>
              {language === "kn"
                ? "ರೈತರಿಗೆ ತಕ್ಷಣದ ಪರಿಹಾರ ಮತ್ತು ಐಸಿಎಆರ್-ಸಿಪಿಸಿಆರ್‌ಐ ಮಾರ್ಗಸೂಚಿಗಳೊಂದಿಗೆ ಲಭ್ಯವಿರುವ ರೋಗಗಳ ಪಟ್ಟಿ."
                : language === "hi"
                ? "किसानों के लिए त्वरित उपचार और ICAR-CPCRI दिशानिर्देशों के साथ उपलब्ध रोग सूची।"
                : "Descriptions and guidance are references, not proof of model validation. Several classifier categories remain experimental and require independent field data."}
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {SPECIMEN_CASES.map((disease) => (
              <div
                key={disease.id}
                className="rounded-2xl border border-slate-200 dark:border-border bg-white dark:bg-card p-4 sm:p-5 shadow-2xs hover:shadow-sm hover:border-emerald-300 dark:hover:border-emerald-700 transition-all text-left flex flex-col justify-between"
              >
                <div>
                  <div className="aspect-16/10 rounded-xl overflow-hidden mb-3.5 bg-slate-100 dark:bg-slate-800">
                    <img src={disease.image} alt={disease.name[language]} className="w-full h-full object-cover" />
                  </div>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <span className={`w-2 h-2 rounded-full ${disease.tagColor}`} />
                    <span className="text-[11px] font-bold text-slate-500 uppercase">{disease.id}</span>
                  </div>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white leading-tight mb-1.5">
                    {disease.name[language]}
                  </h4>
                  <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed">
                    {disease.problem[language]}
                  </p>
                </div>

                <div className="pt-3 mt-3 border-t border-slate-100 dark:border-border">
                  <Link
                    to={`/detection?sample=${disease.id}`}
                    className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 flex items-center justify-between"
                  >
                    <span>Test In Studio</span>
                    <ChevronRight size={14} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── 6. FINAL CALL TO ACTION ────────────────────────────────────── */}
      <section className="py-14 sm:py-20 bg-emerald-800 text-white relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-emerald-100 text-xs font-medium mb-5">
            <Camera size={14} />
            <span>Zero Hardware Setup Required</span>
          </div>

          <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight mb-4 ${leadingClass}`}>
            {ui.ctaTitle[language]}
          </h2>

          <p className={`text-base sm:text-lg text-emerald-100/90 leading-relaxed max-w-2xl mx-auto mb-8 ${leadingClass}`}>
            {ui.ctaDesc[language]}
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 max-w-md mx-auto">
            <Link
              to="/detection"
              className="w-full sm:w-auto h-12 px-7 rounded-xl bg-white text-emerald-800 font-bold text-sm hover:bg-emerald-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              <Camera size={18} />
              <span>{ui.primaryCta[language]}</span>
            </Link>

            <Link
              to="/diseases"
              className="w-full sm:w-auto h-12 px-6 rounded-xl border border-white/30 text-white font-semibold text-sm hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
            >
              <BookOpen size={16} />
              <span>Browse Disease Library</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ─── 7. BOTANICAL FOOTER ────────────────────────────────────────── */}
      <footer id="about" className="border-t border-slate-200 dark:border-border bg-white dark:bg-card py-12 text-slate-600 dark:text-slate-400 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10 text-left">
            {/* Col 1: Brand */}
            <div className="col-span-2 md:col-span-1 space-y-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-700 flex items-center justify-center text-white">
                  <Leaf size={16} />
                </div>
                <span className="font-bold text-base text-slate-900 dark:text-white">ArecaVision AI</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Precision Agricultural Artificial Intelligence engineered for early detection of arecanut pathologies.
              </p>
            </div>

            {/* Col 2: Diagnostics */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] mb-3">
                Diagnostics
              </h5>
              <ul className="space-y-2">
                <li><Link to="/detection" className="hover:text-emerald-700">Detection Studio</Link></li>
                <li><Link to="/diseases" className="hover:text-emerald-700">Pathology Library</Link></li>
                <li><Link to="/history" className="hover:text-emerald-700">Scan Records</Link></li>
                <li><Link to="/analytics" className="hover:text-emerald-700">Analytics Twin</Link></li>
              </ul>
            </div>

            {/* Col 3: Research */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] mb-3">
                Architecture
              </h5>
              <ul className="space-y-2">
                <li><span className="text-slate-500">Stage 1: EfficientNet-B0</span></li>
                <li><span className="text-slate-500">Stage 2: YOLOv8n Bounding</span></li>
                <li><span className="text-slate-500">Stage 3: ViT-B/16 Multi-TTA</span></li>
                <li><Link to="/research" className="hover:text-emerald-700">Research Benchmarks</Link></li>
              </ul>
            </div>

            {/* Col 4: Agricultural Advisory */}
            <div>
              <h5 className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] mb-3">
                Protocol Standards
              </h5>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                Spray schedules and dosages are aligned with recommendations from ICAR-CPCRI and UAS Dharwad agronomy packages of practice.
              </p>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-200/80 dark:border-border/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-500 text-[11px]">
            <p>© {new Date().getFullYear()} ArecaVision AI. All rights reserved. Field diagnostics tool for arecanut growers.</p>
            <p>Non-destructive early detection system • Offline-resilient client caching</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
