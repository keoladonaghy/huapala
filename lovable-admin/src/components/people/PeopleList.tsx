import { useState } from "react";
import { Person } from "@/types/people";
import { realPeopleData } from "@/data/mockPeople";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PersonFormModal } from "./PersonFormModal";
import { Plus, Search, Edit2, Calendar, User } from "lucide-react";

export function PeopleList() {
  const [people, setPeople] = useState<Person[]>(realPeopleData);
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPerson, setEditingPerson] = useState<Person | null>(null);

  const filteredPeople = people.filter(person =>
    person.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.roles.some(role => role.toLowerCase().includes(searchTerm.toLowerCase())) ||
    person.specialties.some(specialty => specialty.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (person.place_of_birth && person.place_of_birth.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (person.cultural_background && person.cultural_background.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleAddPerson = (newPerson: Omit<Person, "person_id">) => {
    const person: Person = {
      ...newPerson,
      person_id: Date.now().toString(),
    };
    setPeople([...people, person]);
  };

  const handleEditPerson = (updatedPerson: Omit<Person, "person_id">) => {
    if (editingPerson) {
      const person: Person = {
        ...updatedPerson,
        person_id: editingPerson.person_id,
      };
      setPeople(people.map(p => p.person_id === editingPerson.person_id ? person : p));
      setEditingPerson(null);
    }
  };

  const openEditModal = (person: Person) => {
    setEditingPerson(person);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingPerson(null);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">People Management</h1>
          <p className="text-muted-foreground">Manage composers, performers, and other contributors</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="bg-ocean-deep hover:bg-ocean-deep/90">
          <Plus className="w-4 h-4 mr-2" />
          Add Person
        </Button>
      </div>

      <div className="flex items-center space-x-2">
        <Search className="w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search by name, role, or alias..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredPeople.map((person) => (
          <Card key={person.person_id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-lg">{person.display_name}</CardTitle>
                  {person.full_name !== person.display_name && (
                    <p className="text-sm text-muted-foreground">
                      {person.full_name}
                    </p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => openEditModal(person)}
                >
                  <Edit2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-1">
                <Badge variant="outline" className="text-xs font-medium">
                  {person.primary_role}
                </Badge>
                {person.roles.filter(role => role !== person.primary_role).map((role) => (
                  <Badge key={role} variant="secondary" className="text-xs">
                    {role}
                  </Badge>
                ))}
              </div>
              
              {person.specialties.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {person.specialties.map((specialty) => (
                    <Badge key={specialty} variant="outline" className="text-xs bg-tropical-light/20 text-tropical border-tropical-light">
                      {specialty.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              )}
              
              {(person.birth_date || person.death_date) && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>
                    {person.birth_date}
                    {person.birth_date && person.death_date && " - "}
                    {person.death_date}
                  </span>
                </div>
              )}

              {person.place_of_birth && (
                <div className="text-sm text-muted-foreground">
                  📍 {person.place_of_birth}
                </div>
              )}

              {person.cultural_background && (
                <div className="text-sm">
                  <Badge variant="outline" className="bg-coral-light/20 text-coral border-coral-light">
                    {person.cultural_background}
                  </Badge>
                </div>
              )}

              {person.biographical_notes && (
                <div className="text-sm text-muted-foreground line-clamp-3" 
                     dangerouslySetInnerHTML={{ __html: person.biographical_notes }} />
              )}

              {person.notable_works.length > 0 && (
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground mb-1">Notable Works:</p>
                  <p className="text-xs text-foreground">
                    {person.notable_works.slice(0, 3).join(", ")}
                    {person.notable_works.length > 3 && ` +${person.notable_works.length - 3} more`}
                  </p>
                </div>
              )}

              {person.awards_honors.length > 0 && (
                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground mb-1">Awards:</p>
                  <p className="text-xs text-foreground">
                    {person.awards_honors.slice(0, 2).map(award => award.name).join(", ")}
                    {person.awards_honors.length > 2 && ` +${person.awards_honors.length - 2} more`}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPeople.length === 0 && (
        <div className="text-center py-8">
          <User className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No people found</h3>
          <p className="text-muted-foreground">
            {searchTerm ? "Try adjusting your search terms" : "Start by adding your first person"}
          </p>
        </div>
      )}

      <PersonFormModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSubmit={editingPerson ? handleEditPerson : handleAddPerson}
        person={editingPerson}
      />
    </div>
  );
}