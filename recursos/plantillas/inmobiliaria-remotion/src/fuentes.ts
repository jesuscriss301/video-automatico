import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

const f = (family: string, file: string, weight: string, style = "normal") =>
  loadFont({ family, url: staticFile(`fonts/${file}`), weight, style });

export const fuentesListas = Promise.all([
  f("Poppins", "poppins-latin-500-normal.woff2", "500"),
  f("Poppins", "poppins-latin-700-normal.woff2", "700"),
  f("Poppins", "poppins-latin-800-normal.woff2", "800"),
  f("Lora", "lora-latin-400-normal.woff2", "400"),
  f("Lora", "lora-latin-600-normal.woff2", "600"),
  f("Lora", "lora-latin-400-italic.woff2", "400", "italic"),
  f("JetBrains Mono", "jetbrains-mono-latin-800-normal.woff2", "800"),
]);
