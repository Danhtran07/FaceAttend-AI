import { describe, expect, it } from "vitest";
import { evaluateFaceCaptureQuality } from "./faceQuality";

describe("evaluateFaceCaptureQuality", () => {
  it("accepts a balanced face image with enough contrast", () => {
    const width = 320;
    const height = 240;
    const data = new Uint8ClampedArray(width * height * 4);

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const idx = (y * width + x) * 4;
        const centerBias = Math.abs(x - width / 2) + Math.abs(y - height / 2);
        const base = 120 + Math.max(0, 60 - centerBias * 0.15);
        data[idx] = base;
        data[idx + 1] = base - 10;
        data[idx + 2] = base - 20;
        data[idx + 3] = 255;
      }
    }

    const result = evaluateFaceCaptureQuality({ data, width, height });
    expect(result.valid).toBe(true);
    expect(result.score).toBeGreaterThan(60);
  });

  it("rejects dark or flat images with poor contrast", () => {
    const width = 320;
    const height = 240;
    const data = new Uint8ClampedArray(width * height * 4);

    for (let i = 0; i < data.length; i += 4) {
      const value = 12;
      data[i] = value;
      data[i + 1] = value;
      data[i + 2] = value;
      data[i + 3] = 255;
    }

    const result = evaluateFaceCaptureQuality({ data, width, height });
    expect(result.valid).toBe(false);
    expect(result.message.toLowerCase()).toMatch(/lighting|contrast|quality|brightness|capture|face|center/i);
  });
});
