import { useState, useEffect } from "react";
import { Person, PersonFormData } from "@/types/people";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { X, Plus } from "lucide-react";

interface PersonFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (person: Omit<Person, "person_id">) => void;
  person?: Person | null;
}

const defaultRoles = ["composer", "lyricist", "performer", "vocalist", "musician", "arranger", "producer", "translator", "editor", "source_contributor"];
const verificationStatuses = ["unverified", "verified", "needs_review", "disputed"];

export function PersonFormModal({ isOpen, onClose, onSubmit, person }: PersonFormModalProps) {
  const [formData, setFormData] = useState<PersonFormData>({
    full_name: "",
    display_name: "",
    place_of_birth: "",
    places_of_hawaiian_influence: "",
    primary_influence_location: "",
    hawaiian_speaker: null,
    birth_date: "",
    death_date: "",
    cultural_background: "",
    biographical_notes: "",
    roles: [],
    primary_role: "",
    specialties: "",
    active_period_start: "",
    active_period_end: "",
    notable_works: "",
    awards_honors: "",
    source_references_sources: "",
    source_references_citations: "",
    verification_status: "unverified",
    last_verified_date: "",
  });

  const [newRole, setNewRole] = useState("");

  useEffect(() => {
    if (person) {
      setFormData({
        full_name: person.full_name,
        display_name: person.display_name,
        place_of_birth: person.place_of_birth || "",
        places_of_hawaiian_influence: person.places_of_hawaiian_influence.join(", "),
        primary_influence_location: person.primary_influence_location || "",
        hawaiian_speaker: person.hawaiian_speaker,
        birth_date: person.birth_date || "",
        death_date: person.death_date || "",
        cultural_background: person.cultural_background || "",
        biographical_notes: person.biographical_notes,
        roles: person.roles,
        primary_role: person.primary_role,
        specialties: person.specialties.join(", "),
        active_period_start: person.active_period_start?.toString() || "",
        active_period_end: person.active_period_end?.toString() || "",
        notable_works: person.notable_works.join(", "),
        awards_honors: person.awards_honors.map(award => 
          `${award.name} (${award.awarded_by}, ${award.year})`
        ).join("; "),
        source_references_sources: person.source_references.sources.join(", "),
        source_references_citations: person.source_references.citations.join(", "),
        verification_status: person.verification_status,
        last_verified_date: person.last_verified_date || "",
      });
    } else {
      setFormData({
        full_name: "",
        display_name: "",
        place_of_birth: "",
        places_of_hawaiian_influence: "",
        primary_influence_location: "",
        hawaiian_speaker: null,
        birth_date: "",
        death_date: "",
        cultural_background: "",
        biographical_notes: "",
        roles: [],
        primary_role: "",
        specialties: "",
        active_period_start: "",
        active_period_end: "",
        notable_works: "",
        awards_honors: "",
        source_references_sources: "",
        source_references_citations: "",
        verification_status: "unverified",
        last_verified_date: "",
      });
    }
  }, [person, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.full_name.trim()) return;

    // Parse awards from string format back to structured data
    const parseAwards = (awardsString: string) => {
      if (!awardsString.trim()) return [];
      return awardsString.split(";").map(award => {
        const match = award.trim().match(/^(.+)\s+\((.+),\s*(\d+)\)$/);
        if (match) {
          return {
            name: match[1].trim(),
            awarded_by: match[2].trim(),
            year: parseInt(match[3])
          };
        }
        return {
          name: award.trim(),
          awarded_by: "",
          year: new Date().getFullYear()
        };
      });
    };

    const processedPerson = {
      full_name: formData.full_name.trim(),
      display_name: formData.display_name.trim() || formData.full_name.trim(),
      place_of_birth: formData.place_of_birth.trim() || null,
      places_of_hawaiian_influence: formData.places_of_hawaiian_influence.trim() 
        ? formData.places_of_hawaiian_influence.split(",").map(p => p.trim()).filter(Boolean)
        : [],
      primary_influence_location: formData.primary_influence_location.trim() || null,
      hawaiian_speaker: formData.hawaiian_speaker,
      birth_date: formData.birth_date || null,
      death_date: formData.death_date || null,
      cultural_background: formData.cultural_background.trim() || null,
      biographical_notes: formData.biographical_notes.trim(),
      roles: formData.roles,
      primary_role: formData.primary_role,
      specialties: formData.specialties.trim() 
        ? formData.specialties.split(",").map(s => s.trim()).filter(Boolean)
        : [],
      active_period_start: formData.active_period_start ? parseInt(formData.active_period_start) : null,
      active_period_end: formData.active_period_end ? parseInt(formData.active_period_end) : null,
      notable_works: formData.notable_works.trim() 
        ? formData.notable_works.split(",").map(w => w.trim()).filter(Boolean)
        : [],
      awards_honors: parseAwards(formData.awards_honors),
      source_references: {
        sources: formData.source_references_sources.trim() 
          ? formData.source_references_sources.split(",").map(s => s.trim()).filter(Boolean)
          : [],
        citations: formData.source_references_citations.trim() 
          ? formData.source_references_citations.split(",").map(c => c.trim()).filter(Boolean)
          : []
      },
      verification_status: formData.verification_status,
      last_verified_date: formData.last_verified_date || null,
    };

    onSubmit(processedPerson);
    onClose();
  };

  const addRole = (role: string) => {
    if (role && !formData.roles.includes(role)) {
      const newRoles = [...formData.roles, role];
      setFormData(prev => ({
        ...prev,
        roles: newRoles,
        primary_role: prev.primary_role || role
      }));
    }
  };

  const removeRole = (roleToRemove: string) => {
    const newRoles = formData.roles.filter(role => role !== roleToRemove);
    setFormData(prev => ({
      ...prev,
      roles: newRoles,
      primary_role: prev.primary_role === roleToRemove 
        ? (newRoles[0] || "") 
        : prev.primary_role
    }));
  };

  const addCustomRole = () => {
    if (newRole.trim()) {
      addRole(newRole.trim().toLowerCase());
      setNewRole("");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>
            {person ? "Edit Person" : "Add New Person"}
          </DialogTitle>
          <DialogDescription>
            {person ? "Update person information" : "Add a new person to the database"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex-1 overflow-hidden flex flex-col">
          <Tabs defaultValue="basic" className="flex-1 overflow-hidden flex flex-col">
            <TabsList className="grid w-full grid-cols-4 flex-shrink-0">
              <TabsTrigger value="basic">Basic Info</TabsTrigger>
              <TabsTrigger value="cultural">Cultural & Bio</TabsTrigger>
              <TabsTrigger value="career">Career & Works</TabsTrigger>
              <TabsTrigger value="sources">Sources & Status</TabsTrigger>
            </TabsList>
            
            <div className="flex-1 overflow-y-auto">
              <TabsContent value="basic" className="space-y-4 p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                      placeholder="Enter full name"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="display_name">Display Name</Label>
                    <Input
                      id="display_name"
                      value={formData.display_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, display_name: e.target.value }))}
                      placeholder="How name should be displayed"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="birth_date">Birth Date</Label>
                    <Input
                      id="birth_date"
                      value={formData.birth_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, birth_date: e.target.value }))}
                      placeholder="e.g., September 2, 1838"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="death_date">Death Date</Label>
                    <Input
                      id="death_date"
                      value={formData.death_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, death_date: e.target.value }))}
                      placeholder="e.g., November 11, 1917"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="place_of_birth">Place of Birth</Label>
                    <Input
                      id="place_of_birth"
                      value={formData.place_of_birth}
                      onChange={(e) => setFormData(prev => ({ ...prev, place_of_birth: e.target.value }))}
                      placeholder="e.g., Honolulu, Oʻahu"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cultural_background">Cultural Background</Label>
                    <Input
                      id="cultural_background"
                      value={formData.cultural_background}
                      onChange={(e) => setFormData(prev => ({ ...prev, cultural_background: e.target.value }))}
                      placeholder="e.g., Native Hawaiian, Kanaka 'Ōiwi"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="hawaiian_speaker"
                    checked={formData.hawaiian_speaker === true}
                    onCheckedChange={(checked) => 
                      setFormData(prev => ({ ...prev, hawaiian_speaker: checked ? true : null }))
                    }
                  />
                  <Label htmlFor="hawaiian_speaker">Hawaiian Speaker</Label>
                </div>
              </TabsContent>

              <TabsContent value="cultural" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label htmlFor="places_of_hawaiian_influence">Places of Hawaiian Influence</Label>
                  <Input
                    id="places_of_hawaiian_influence"
                    value={formData.places_of_hawaiian_influence}
                    onChange={(e) => setFormData(prev => ({ ...prev, places_of_hawaiian_influence: e.target.value }))}
                    placeholder="Comma-separated list of places"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="primary_influence_location">Primary Influence Location</Label>
                  <Input
                    id="primary_influence_location"
                    value={formData.primary_influence_location}
                    onChange={(e) => setFormData(prev => ({ ...prev, primary_influence_location: e.target.value }))}
                    placeholder="Main geographic influence"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="biographical_notes">Biographical Notes</Label>
                  <Textarea
                    id="biographical_notes"
                    value={formData.biographical_notes}
                    onChange={(e) => setFormData(prev => ({ ...prev, biographical_notes: e.target.value }))}
                    placeholder="Biographical information and notes"
                    rows={8}
                  />
                </div>
              </TabsContent>

              <TabsContent value="career" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label>Roles</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {formData.roles.map((role) => (
                      <Badge key={role} variant={role === formData.primary_role ? "default" : "secondary"} className="flex items-center gap-1">
                        {role} {role === formData.primary_role && "(primary)"}
                        <button
                          type="button"
                          onClick={() => removeRole(role)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {defaultRoles
                      .filter(role => !formData.roles.includes(role))
                      .map((role) => (
                        <Button
                          key={role}
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => addRole(role)}
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          {role}
                        </Button>
                      ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                      placeholder="Add custom role"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addCustomRole();
                        }
                      }}
                    />
                    <Button type="button" onClick={addCustomRole} variant="outline">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {formData.roles.length > 1 && (
                  <div className="space-y-2">
                    <Label htmlFor="primary_role">Primary Role</Label>
                    <Select value={formData.primary_role} onValueChange={(value) => 
                      setFormData(prev => ({ ...prev, primary_role: value }))
                    }>
                      <SelectTrigger>
                        <SelectValue placeholder="Select primary role" />
                      </SelectTrigger>
                      <SelectContent>
                        {formData.roles.map((role) => (
                          <SelectItem key={role} value={role}>
                            {role}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="specialties">Specialties</Label>
                  <Input
                    id="specialties"
                    value={formData.specialties}
                    onChange={(e) => setFormData(prev => ({ ...prev, specialties: e.target.value }))}
                    placeholder="Comma-separated specialties (e.g., hawaiian_text_editing, traditional_chant)"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="active_period_start">Active Period Start</Label>
                    <Input
                      id="active_period_start"
                      type="number"
                      value={formData.active_period_start}
                      onChange={(e) => setFormData(prev => ({ ...prev, active_period_start: e.target.value }))}
                      placeholder="e.g., 1915"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="active_period_end">Active Period End</Label>
                    <Input
                      id="active_period_end"
                      type="number"
                      value={formData.active_period_end}
                      onChange={(e) => setFormData(prev => ({ ...prev, active_period_end: e.target.value }))}
                      placeholder="Leave blank if still active"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notable_works">Notable Works</Label>
                  <Textarea
                    id="notable_works"
                    value={formData.notable_works}
                    onChange={(e) => setFormData(prev => ({ ...prev, notable_works: e.target.value }))}
                    placeholder="Comma-separated list of notable works"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="awards_honors">Awards & Honors</Label>
                  <Textarea
                    id="awards_honors"
                    value={formData.awards_honors}
                    onChange={(e) => setFormData(prev => ({ ...prev, awards_honors: e.target.value }))}
                    placeholder="Format: Award Name (Awarding Body, Year); Another Award (Body, Year)"
                    rows={3}
                  />
                  <p className="text-xs text-muted-foreground">
                    Example: Grammy Award (Recording Academy, 2020); Lifetime Achievement (Hawaiian Music Hall of Fame, 2015)
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="sources" className="space-y-4 p-4">
                <div className="space-y-2">
                  <Label htmlFor="source_references_sources">Sources</Label>
                  <Textarea
                    id="source_references_sources"
                    value={formData.source_references_sources}
                    onChange={(e) => setFormData(prev => ({ ...prev, source_references_sources: e.target.value }))}
                    placeholder="Comma-separated list of sources"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="source_references_citations">Citations</Label>
                  <Textarea
                    id="source_references_citations"
                    value={formData.source_references_citations}
                    onChange={(e) => setFormData(prev => ({ ...prev, source_references_citations: e.target.value }))}
                    placeholder="Comma-separated list of citations"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="verification_status">Verification Status</Label>
                    <Select value={formData.verification_status} onValueChange={(value) => 
                      setFormData(prev => ({ ...prev, verification_status: value }))
                    }>
                      <SelectTrigger>
                        <SelectValue placeholder="Select verification status" />
                      </SelectTrigger>
                      <SelectContent>
                        {verificationStatuses.map((status) => (
                          <SelectItem key={status} value={status}>
                            {status.replace(/_/g, ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="last_verified_date">Last Verified Date</Label>
                    <Input
                      id="last_verified_date"
                      type="date"
                      value={formData.last_verified_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, last_verified_date: e.target.value }))}
                    />
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>

          <DialogFooter className="flex-shrink-0 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" className="bg-ocean-deep hover:bg-ocean-deep/90">
              {person ? "Update Person" : "Add Person"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}