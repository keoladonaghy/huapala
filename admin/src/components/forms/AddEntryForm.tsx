import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Music, User, Album, Save } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function AddEntryForm() {
  const [entryType, setEntryType] = useState("song");
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically send data to your API
    toast({
      title: "Entry Added",
      description: `New ${entryType} has been added to the database.`,
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Add New Entry</h1>
        <p className="text-muted-foreground">Add songs, artists, or albums to the Hawaiian music database</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <Button
          variant={entryType === "song" ? "default" : "outline"}
          onClick={() => setEntryType("song")}
          className={`flex items-center gap-2 ${entryType === "song" ? "bg-ocean-deep text-white" : "border-ocean-light text-ocean-deep hover:bg-ocean-light/10"}`}
        >
          <Music className="h-4 w-4" />
          Add Song/Mele
        </Button>
        <Button
          variant={entryType === "artist" ? "default" : "outline"}
          onClick={() => setEntryType("artist")}
          className={`flex items-center gap-2 ${entryType === "artist" ? "bg-coral text-white" : "border-coral text-coral hover:bg-coral-light/10"}`}
        >
          <User className="h-4 w-4" />
          Add Artist
        </Button>
        <Button
          variant={entryType === "album" ? "default" : "outline"}
          onClick={() => setEntryType("album")}
          className={`flex items-center gap-2 ${entryType === "album" ? "bg-tropical text-white" : "border-tropical text-tropical hover:bg-tropical-light/10"}`}
        >
          <Album className="h-4 w-4" />
          Add Album
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {entryType === "song" && <Music className="h-5 w-5 text-ocean-deep" />}
            {entryType === "artist" && <User className="h-5 w-5 text-coral" />}
            {entryType === "album" && <Album className="h-5 w-5 text-tropical" />}
            {entryType === "song" && "Song/Mele Information"}
            {entryType === "artist" && "Artist Information"}
            {entryType === "album" && "Album Information"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {entryType === "song" && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Hawaiian Title *</Label>
                    <Input id="title" placeholder="e.g., Aloha 'Oe" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="englishTitle">English Title</Label>
                    <Input id="englishTitle" placeholder="e.g., Farewell to You" />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="composer">Composer *</Label>
                    <Input id="composer" placeholder="e.g., Queen Lili'uokalani" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="year">Year</Label>
                    <Input id="year" type="number" placeholder="e.g., 1878" />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="genre">Genre</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select genre" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="traditional">Traditional</SelectItem>
                        <SelectItem value="contemporary">Contemporary</SelectItem>
                        <SelectItem value="hula">Hula</SelectItem>
                        <SelectItem value="cover">Cover</SelectItem>
                        <SelectItem value="chant">Chant/Oli</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="key">Musical Key</Label>
                    <Input id="key" placeholder="e.g., C Major" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lyrics">Hawaiian Lyrics</Label>
                  <Textarea 
                    id="lyrics" 
                    placeholder="Enter Hawaiian lyrics here..."
                    className="min-h-[120px]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="translation">English Translation</Label>
                  <Textarea 
                    id="translation" 
                    placeholder="Enter English translation here..."
                    className="min-h-[120px]"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch id="isHawaiian" />
                  <Label htmlFor="isHawaiian">Song is in Hawaiian language</Label>
                </div>
              </>
            )}

            {entryType === "artist" && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="artistName">Artist Name *</Label>
                    <Input id="artistName" placeholder="e.g., Israel Kamakawiwoʻole" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="birthYear">Birth Year</Label>
                    <Input id="birthYear" type="number" placeholder="e.g., 1959" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="biography">Biography</Label>
                  <Textarea 
                    id="biography" 
                    placeholder="Enter artist biography..."
                    className="min-h-[120px]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="instruments">Instruments</Label>
                  <Input id="instruments" placeholder="e.g., Ukulele, Guitar, Vocals" />
                </div>
              </>
            )}

            {entryType === "album" && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="albumTitle">Album Title *</Label>
                    <Input id="albumTitle" placeholder="e.g., Facing Future" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="releaseYear">Release Year</Label>
                    <Input id="releaseYear" type="number" placeholder="e.g., 1993" />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="recordLabel">Record Label</Label>
                    <Input id="recordLabel" placeholder="e.g., Mountain Apple Company" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="producer">Producer</Label>
                    <Input id="producer" placeholder="e.g., Jon de Mello" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Album Description</Label>
                  <Textarea 
                    id="description" 
                    placeholder="Enter album description..."
                    className="min-h-[120px]"
                  />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="notes">Additional Notes</Label>
              <Textarea 
                id="notes" 
                placeholder="Any additional information or cultural context..."
                className="min-h-[80px]"
              />
            </div>

            <div className="flex gap-4">
              <Button 
                type="submit"
                className="bg-gradient-to-r from-ocean-deep to-ocean-light hover:from-ocean-light hover:to-tropical shadow-ocean"
              >
                <Save className="h-4 w-4 mr-2" />
                Save Entry
              </Button>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}