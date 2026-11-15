import { describe, expect, it } from "vitest";
import { initialHeaderState, nextHeaderState } from "./scroll-header-state";

describe("scroll header visibility", () => {
  it("starts transparent at the top and hidden on restored scrolled pages", () => {
    expect(initialHeaderState(0).mode).toBe("top");
    expect(initialHeaderState(600).mode).toBe("hidden");
  });

  it("never shows the floating bar while moving down from the hero", () => {
    let state = initialHeaderState(0);
    for (const y of [1, 60, 79, 80, 81, 82, 160, 400, 900]) {
      state = nextHeaderState(state, y);
      expect(state.mode).toBe(y <= 80 ? "top" : "hidden");
    }
  });

  it("reveals after cumulative upward movement and hides on a one-pixel reversal", () => {
    let state = initialHeaderState(500);
    for (const y of [499, 496, 493]) state = nextHeaderState(state, y);
    expect(state.mode).toBe("hidden");
    state = nextHeaderState(state, 492);
    expect(state.mode).toBe("floating");
    expect(nextHeaderState(state, 493).mode).toBe("hidden");
  });

  it("returns to only the transparent navigation near the top", () => {
    let state = nextHeaderState(initialHeaderState(200), 180);
    expect(state.mode).toBe("floating");
    for (const y of [80, 20, 0, -10]) {
      state = nextHeaderState(state, y);
      expect(state.mode).toBe("top");
    }
    expect(nextHeaderState(state, 100).mode).toBe("hidden");
  });

  it("does not reveal on resize and resets upward distance after scrolling down", () => {
    const hidden = initialHeaderState(500);
    expect(nextHeaderState(hidden, 500).mode).toBe("hidden");
    const floating = nextHeaderState(hidden, 480);
    const down = nextHeaderState(floating, 481);
    expect(nextHeaderState(down, 480).mode).toBe("hidden");
    expect(nextHeaderState(down, 473).mode).toBe("floating");
  });
});
