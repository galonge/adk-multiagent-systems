// V2 feature flag — controls model selector, theme toggle, Gemma 4 support
// set NEXT_PUBLIC_ENABLE_WEALTHPILOT_V2=true to enable

export const V2 = process.env.NEXT_PUBLIC_ENABLE_WEALTHPILOT_V2 === "true";
