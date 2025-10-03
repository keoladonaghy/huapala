import { CanonicalMele, MeleVerse, ProcessingMetadata } from "@/types/mele";
import { Person } from "@/types/people";

// Interface for the real data structure from docs/songs-data.json
interface RealSongData {
  canonical_mele_id: string;
  canonical_title_hawaiian: string;
  canonical_title_english?: string | null;
  primary_composer?: string | null;
  primary_lyricist?: string | null;
  translator?: string | null;
  source_file?: string | null;
  estimated_composition_date?: string | null;
  cultural_significance_notes?: string | null;
  composer?: string | null;
  hawaiian_editor?: string | null;
  source_publication?: string | null;
  copyright_info?: string | null;
  primary_location?: string | null;
  island?: string | null;
  themes?: string | null;
  mele_type?: string | null;
  cultural_elements?: string | null;
  // Add other fields as they appear in the real data
  [key: string]: any;
}

export async function loadRealSongData(): Promise<CanonicalMele[]> {
  try {
    // In production (GitHub Pages), load from static data
    const response = await fetch('/data/songs-data.json');
    if (!response.ok) {
      throw new Error(`Failed to load song data: ${response.status}`);
    }
    const realData: RealSongData[] = await response.json();
    
    return realData.map(adaptSongData);
  } catch (error) {
    console.error('Error loading real song data:', error);
    // Return empty array as fallback
    return [];
  }
}

export function adaptSongData(realSong: RealSongData): CanonicalMele {
  // Create mock processing metadata since it's not in the real data
  const processing_metadata: ProcessingMetadata = {
    exported_at: new Date().toISOString(),
    source: "real_data_adapter",
    total_sections: 1,
    total_lines: 0
  };

  // Create mock verses since the real data structure doesn't include verse details
  const verses: MeleVerse[] = [
    {
      id: "v1",
      order: 1,
      type: "verse" as const,
      number: 1,
      label: "Verse 1:",
      hawaiian_lines: ["Loading verse data..."],
      english_lines: ["Verse data will be loaded separately"]
    }
  ];

  return {
    canonical_mele_id: realSong.canonical_mele_id,
    canonical_title_hawaiian: realSong.canonical_title_hawaiian,
    canonical_title_english: realSong.canonical_title_english || "",
    primary_composer: realSong.primary_composer || realSong.composer || "Unknown",
    translator: realSong.translator || "",
    source_file: realSong.source_file || "",
    processing_metadata,
    verses
  };
}

// For now, return empty people data until we have real people data to adapt
export async function loadRealPeopleData(): Promise<Person[]> {
  try {
    // TODO: Implement when we have real people data source
    // For now, return empty array to prevent build errors
    return [];
  } catch (error) {
    console.error('Error loading people data:', error);
    return [];
  }
}