export interface Award {
  name: string;
  awarded_by: string;
  year: number;
}

export interface SourceReferences {
  sources: string[];
  citations: string[];
}

export interface Person {
  person_id: string;
  full_name: string;
  display_name: string;
  place_of_birth: string | null;
  places_of_hawaiian_influence: string[];
  primary_influence_location: string | null;
  hawaiian_speaker: boolean | null;
  birth_date: string | null;
  death_date: string | null;
  cultural_background: string | null;
  biographical_notes: string;
  roles: string[];
  primary_role: string;
  specialties: string[];
  active_period_start: number | null;
  active_period_end: number | null;
  notable_works: string[];
  awards_honors: Award[];
  source_references: SourceReferences;
  verification_status: string;
  last_verified_date: string | null;
}

export interface PersonFormData {
  full_name: string;
  display_name: string;
  place_of_birth: string;
  places_of_hawaiian_influence: string;
  primary_influence_location: string;
  hawaiian_speaker: boolean | null;
  birth_date: string;
  death_date: string;
  cultural_background: string;
  biographical_notes: string;
  roles: string[];
  primary_role: string;
  specialties: string;
  active_period_start: string;
  active_period_end: string;
  notable_works: string;
  awards_honors: string;
  source_references_sources: string;
  source_references_citations: string;
  verification_status: string;
  last_verified_date: string;
}