import { useTheme } from "../theme/ThemeProvider";

export default function Logo(props) {
  const { theme } = useTheme();
  const ThemeLogo = theme?.Logo;

  if (!ThemeLogo) return null;
  return <ThemeLogo {...props} />;
}
