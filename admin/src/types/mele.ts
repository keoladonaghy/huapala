export interface MeleLine {
  id: string;
  line_number: number;
  hawaiian_text: string;
  english_text: string;
  is_bilingual: boolean;
}

export interface MeleVerse {
  id?: string;
  type: "verse" | "chorus";
  number?: number;
  order: number;
  label?: string;
  lines?: MeleLine[];
  // Alternative structure for some songs
  hawaiian_text?: string;
  english_text?: string;
  hawaiian_lines?: string[];
  english_lines?: string[];
}

export interface ProcessingMetadata {
  original_file?: string;
  exported_at?: string;
  source?: string;
  processed_at?: string;
  parsing_quality_score?: number;
  total_sections: number;
  total_lines: number;
}

export interface CanonicalMele {
  canonical_mele_id: string;
  canonical_title_hawaiian: string;
  canonical_title_english: string;
  primary_composer: string;
  translator: string;
  source_file: string;
  processing_metadata: ProcessingMetadata;
  verses: MeleVerse[];
}

export interface MeleFormData {
  canonical_title_hawaiian: string;
  canonical_title_english: string;
  primary_composer: string;
  translator: string;
  source_file: string;
  original_file: string;
  exported_at: string;
  source: string;
  processed_at: string;
  parsing_quality_score: string;
  total_sections: string;
  total_lines: string;
  verses_summary: string; // Brief summary instead of full verse data
}