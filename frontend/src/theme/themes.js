import SaintsLogo from "../components/logos/SaintsLogo";
import NoirLogo from "../components/logos/NoirLogo";
import RoseLogo from "../components/logos/RoseLogo";
import CyberpunkLogo from "../components/logos/CyberpunkLogo";
import WitcherLogo from "../components/logos/WitcherLogo";

export const THEMES = [
  {
    id: "saints",
    name: "Saints",
    Logo: SaintsLogo,
  },
  {
    id: "noir",
    name: "Noir",
    Logo: NoirLogo,
  },
  {
    id: "rose",
    name: "Rose",
    Logo: RoseLogo,
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk",
    Logo: CyberpunkLogo,
  },
  {
    id: "witcher",
    name: "Witcher",
    Logo: WitcherLogo,
  },
];

export const DEFAULT_THEME_ID = "saints";

export function getThemeById(themeId) {
  return THEMES.find((t) => t.id === themeId) || THEMES[0];
}
