import { afterEach, describe, expect, it, vi } from "vitest";
import { ServiceError } from "@/lib/api";
import { demoFields } from "./index";
import { fromApiField, loadField, loadFieldData } from "./load";

const item = (overrides = {}) => ({
  field_id: "test-005",
  county: "Story" as const,
  role: "test" as const,
  boundary_source: "demo" as const,
  area_ha: 17.6,
  geometry: {
    coordinates: [
      [
        [1, 2],
        [3, 4],
        [1, 2],
      ],
    ],
  },
  field_class: "continuous_corn",
  domain_note: "out-of-domain: continuous corn",
  provenance: "demo",
  cover_detail: null,
  centroid: [1.5, 2.5] as [number, number],
  ...overrides,
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("fromApiField", () => {
  it("maps the service's field to the shape the screens use", () => {
    const field = fromApiField(item());
    expect(field).toMatchObject({
      id: "test-005",
      county: "Story",
      fieldClass: "corn", // DS1's continuous_corn, shown as "corn"
      areaHa: 17.6,
      centroid: [1.5, 2.5],
    });
    expect(field.ring).toEqual([
      [1, 2],
      [3, 4],
      [1, 2],
    ]);
  });

  it.each([
    ["rotation", "rotation"],
    ["pasture_hay", "pasture"],
    ["mixed", "mixed"],
    [null, "mixed"],
  ])("shows class %s as %s", (given, shown) => {
    expect(fromApiField(item({ field_class: given })).fieldClass).toBe(shown);
  });
});

describe("loadFieldData", () => {
  it("uses the web app's own files when no service is configured, and calls nothing", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const data = await loadFieldData();
    expect(data.fields).toBe(demoFields);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reads the fields and county outlines from the service when one is configured", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (url: string) =>
          new Response(
            JSON.stringify(
              url.endsWith("/fields/demo")
                ? [item()]
                : {
                    counties: [
                      {
                        county: "Boone",
                        ring: [
                          [0, 0],
                          [1, 1],
                          [0, 0],
                        ],
                      },
                    ],
                  },
            ),
          ),
      ),
    );
    const data = await loadFieldData();
    expect(data.fields.map((f) => f.id)).toEqual(["test-005"]);
    expect(data.counties[0].county).toBe("Boone");
    expect((await loadField("test-005"))?.id).toBe("test-005");
    expect(await loadField("nope")).toBeUndefined();
  });

  it("fails visibly rather than falling back to local files when the service is down", async () => {
    vi.stubEnv("AGROCYCLE_API_URL", "http://api");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 500 })),
    );
    await expect(loadFieldData()).rejects.toThrow(ServiceError);
  });
});
