export interface ExtractedString {
  key: string;
  default_value: string;
  source_file: string;
  line: number;
  context: string;
}

export interface ExtractorOptions {
  src: string;
  out: string;
  /** When true, throw on malformed t() calls; otherwise skip silently. */
  strict?: boolean;
}
