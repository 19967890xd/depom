import { Config } from "@remotion/cli/config";

Config.setEntryPoint("src/index.ts");
// Three.js için WebGL gerekli; headless ortamda SwiftShader (swangle) kullan
Config.setChromiumOpenGlRenderer("swangle");
Config.setVideoImageFormat("jpeg");
