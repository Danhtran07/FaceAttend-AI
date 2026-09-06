export interface FaceCaptureQualityResult {
  valid: boolean;
  score: number;
  message: string;
  brightness: number;
  contrast: number;
}

export type FaceImageDataLike = {
  data: Uint8ClampedArray | Uint8Array;
  width: number;
  height: number;
};

export function evaluateFaceCaptureQuality(imageData: ImageData | FaceImageDataLike): FaceCaptureQualityResult {
  const { data, width, height } = imageData;
  if (width === 0 || height === 0) {
    return {
      valid: false,
      score: 0,
      message: "Capture failed. Please try again.",
      brightness: 0,
      contrast: 0,
    };
  }

  let brightnessSum = 0;
  let contrastSum = 0;
  let sampleCount = 0;

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    brightnessSum += luminance;
    sampleCount += 1;

    const localContrast = Math.abs(r - g) + Math.abs(g - b) + Math.abs(r - b);
    contrastSum += localContrast / 765;
  }

  const brightness = (brightnessSum / sampleCount) * 100;
  const contrast = (contrastSum / sampleCount) * 100;

  const centeredFaceBias = Math.min(width, height) * 0.16;
  const faceCenterX = width / 2;
  const faceCenterY = height / 2;
  let centerEnergy = 0;
  let totalEnergy = 0;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = (y * width + x) * 4;
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
      const dx = Math.abs(x - faceCenterX);
      const dy = Math.abs(y - faceCenterY);
      const distance = Math.sqrt(dx * dx + dy * dy);

      totalEnergy += luminance;
      if (distance <= centeredFaceBias) {
        centerEnergy += luminance;
      }
    }
  }

  const faceCenterRatio = totalEnergy > 0 ? (centerEnergy / totalEnergy) * 100 : 0;
  const qualityScore = (
    (brightness >= 20 && brightness <= 80 ? 38 : 12) +
    (contrast >= 12 ? 28 : 8) +
    (faceCenterRatio >= 12 ? 20 : 8) +
    (brightness >= 35 && brightness <= 70 ? 14 : 4)
  );

  if (brightness < 12 || brightness > 88) {
    return {
      valid: false,
      score: qualityScore,
      message: "Lighting is not suitable. Please move to a brighter or more even area.",
      brightness,
      contrast,
    };
  }

  if (contrast < 4) {
    return {
      valid: false,
      score: qualityScore,
      message: "Face image quality is too low. Please capture a clearer face photo.",
      brightness,
      contrast,
    };
  }

  if (faceCenterRatio < 10) {
    return {
      valid: false,
      score: qualityScore,
      message: "Please keep your face centered in the frame.",
      brightness,
      contrast,
    };
  }

  return {
    valid: qualityScore >= 55,
    score: Math.max(0, Math.min(100, qualityScore)),
    message:
      qualityScore >= 55
        ? "Face quality is good enough to enroll."
        : "Please take a clearer face image with better lighting and centering.",
    brightness,
    contrast,
  };
}
