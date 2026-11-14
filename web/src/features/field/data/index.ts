import countiesData from "./counties.generated.json";
import fieldsData from "./fields.generated.json";
import type { County, DemoField } from "../types";

/** Read-only view over the generated data. See `scripts/sync-field-data.mjs`. */
export const demoFields = fieldsData.fields as unknown as readonly DemoField[];
export const counties = countiesData.counties as unknown as readonly County[];

export const PRIMARY_FIELD_ID = "primary-001";

const byId = new Map(demoFields.map((field) => [field.id, field]));

export function getFieldById(id: string | null | undefined): DemoField | undefined {
  return id ? byId.get(id) : undefined;
}
