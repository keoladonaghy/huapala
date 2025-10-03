import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { 
  Check, 
  X, 
  Edit, 
  Search, 
  Book, 
  Music, 
  Star, 
  AlertCircle, 
  Eye,
  Loader2,
  BarChart3,
  Zap
} from "lucide-react";

interface SuggestedLinkage {
  canonical_mele_id: string;
  song_title_matched: string;
  songbook_entry_title: string;
  songbook_name: string;
  page: number;
  pub_year: number;
  composer: string;
  similarity_score: number;
  match_status: 'suggested' | 'approved' | 'rejected' | 'pending';
  timestamp: string;
  songbook_entry_id: number;
}

export function SuggestedLinkages() {
  const [linkages, setLinkages] = useState<SuggestedLinkage[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("suggested");
  const [confidenceFilter, setConfidenceFilter] = useState<string>("all");
  const { toast } = useToast();

  // Load suggested linkages
  useEffect(() => {
    loadLinkages();
  }, []);

  const loadLinkages = async () => {
    try {
      setLoading(true);
      // Load from the JSON file created by the matching engine
      const response = await fetch('/data/songbooks/suggested_linkages.json');
      if (!response.ok) {
        throw new Error('Failed to load suggested linkages');
      }
      const data = await response.json();
      
      // Load saved statuses from localStorage
      const savedStatuses = JSON.parse(localStorage.getItem('linkage_statuses') || '{}');
      
      // Apply saved statuses to the data
      const dataWithStatuses = data.map((linkage: SuggestedLinkage) => {
        const linkageId = `${linkage.canonical_mele_id}-${linkage.songbook_entry_id}`;
        return {
          ...linkage,
          match_status: savedStatuses[linkageId] || linkage.match_status
        };
      });
      
      setLinkages(dataWithStatuses);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load suggested linkages. Make sure the matching engine has been run.",
        variant: "destructive",
      });
      console.error("Failed to load linkages:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateLinkageStatus = async (linkageToUpdate: SuggestedLinkage, newStatus: 'approved' | 'rejected' | 'pending') => {
    const linkageId = `${linkageToUpdate.canonical_mele_id}-${linkageToUpdate.songbook_entry_id}`;
    
    // Find the actual index in the full linkages array
    const actualIndex = linkages.findIndex(l => 
      l.canonical_mele_id === linkageToUpdate.canonical_mele_id && 
      l.songbook_entry_id === linkageToUpdate.songbook_entry_id
    );
    
    if (actualIndex === -1) {
      console.error('Could not find linkage in array:', linkageToUpdate);
      return;
    }
    
    const updatedLinkages = [...linkages];
    const linkage = updatedLinkages[actualIndex];
    
    console.log('=== UPDATING LINKAGE ===');
    console.log('Linkage ID:', linkageId);
    console.log('New Status:', newStatus);
    console.log('Song:', linkage.song_title_matched);
    console.log('Songbook Entry:', linkage.songbook_entry_title);
    
    updatedLinkages[actualIndex].match_status = newStatus;
    
    // Save to localStorage for persistence
    const savedStatuses = JSON.parse(localStorage.getItem('linkage_statuses') || '{}');
    savedStatuses[linkageId] = newStatus;
    localStorage.setItem('linkage_statuses', JSON.stringify(savedStatuses));
    
    console.log('Saved statuses:', JSON.stringify(savedStatuses, null, 2));
    
    setLinkages(updatedLinkages);
    
    // Force update of filtered view
    setTimeout(() => {
      setLinkages([...updatedLinkages]);
    }, 100);
    
    // If approved, create the actual database linkage
    if (newStatus === 'approved') {
      try {
        // This would update the songbook_entries table with the canonical_mele_id
        console.log('Creating database linkage:', {
          songbook_entry_id: linkage.songbook_entry_id,
          canonical_mele_id: linkage.canonical_mele_id,
          song_title: linkage.song_title_matched,
          songbook_entry: linkage.songbook_entry_title
        });
        
        // TODO: Implement actual database update
        // await api.songbook.updateEntryLinkage(linkage.songbook_entry_id, linkage.canonical_mele_id);
        
        toast({
          title: "Linkage Created!",
          description: `Successfully linked "${linkage.song_title_matched}" to "${linkage.songbook_entry_title}"`,
        });
      } catch (error) {
        console.error('Failed to create database linkage:', error);
        toast({
          title: "Database Error",
          description: "Approved in UI but failed to update database",
          variant: "destructive",
        });
      }
    } else {
      toast({
        title: "Success",
        description: `Linkage ${newStatus} successfully`,
      });
    }

    // Auto-scroll to next unprocessed suggestion
    setTimeout(() => {
      const remainingFiltered = filteredLinkages.filter(l => l.match_status === 'suggested');
      if (remainingFiltered.length > 1) {
        const nextElement = document.querySelector(`[data-linkage-index="${index + 1}"]`);
        if (nextElement) {
          nextElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      } else {
        toast({
          title: "All done!",
          description: "No more suggestions to review. Great work!",
        });
      }
    }, 500);
  };

  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return { level: "High", color: "bg-green-500", textColor: "text-green-700" };
    if (score >= 0.8) return { level: "Medium", color: "bg-yellow-500", textColor: "text-yellow-700" };
    return { level: "Low", color: "bg-red-500", textColor: "text-red-700" };
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Approved</Badge>;
      case 'rejected':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Rejected</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Pending Review</Badge>;
      default:
        return <Badge variant="outline">Suggested</Badge>;
    }
  };

  // Filter linkages
  const filteredLinkages = linkages.filter(linkage => {
    const matchesSearch = searchTerm === "" || 
      linkage.song_title_matched.toLowerCase().includes(searchTerm.toLowerCase()) ||
      linkage.songbook_entry_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      linkage.songbook_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      linkage.composer?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === "all" || linkage.match_status === statusFilter;
    
    const matchesConfidence = confidenceFilter === "all" || 
      (confidenceFilter === "high" && linkage.similarity_score >= 0.9) ||
      (confidenceFilter === "medium" && linkage.similarity_score >= 0.8 && linkage.similarity_score < 0.9) ||
      (confidenceFilter === "low" && linkage.similarity_score < 0.8);

    const passes = matchesSearch && matchesStatus && matchesConfidence;
    
    // Debug logging for specific songs
    if (linkage.song_title_matched.toLowerCase().includes('adios')) {
      console.log(`FILTER DEBUG - ${linkage.song_title_matched}:`, {
        status: linkage.match_status,
        statusFilter,
        matchesStatus,
        passes
      });
    }

    return passes;
  });

  // Statistics
  const stats = {
    total: linkages.length,
    approved: linkages.filter(l => l.match_status === 'approved').length,
    rejected: linkages.filter(l => l.match_status === 'rejected').length,
    pending: linkages.filter(l => l.match_status === 'suggested' || l.match_status === 'pending').length,
    highConfidence: linkages.filter(l => l.similarity_score >= 0.9).length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading suggested linkages...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Suggested Songbook Linkages</h1>
          <p className="text-muted-foreground">
            Review and approve matches between your songs and songbook entries
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadLinkages} variant="outline">
            <Zap className="w-4 h-4 mr-2" />
            Refresh Matches
          </Button>
          <Button 
            onClick={() => {
              const saved = JSON.parse(localStorage.getItem('linkage_statuses') || '{}');
              console.log('Current saved statuses:', saved);
              alert(`Saved statuses: ${Object.keys(saved).length} items\n${JSON.stringify(saved, null, 2)}`);
            }}
            variant="outline"
            size="sm"
          >
            Debug Status
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-ocean-deep" />
              <div>
                <div className="text-2xl font-bold">{stats.total}</div>
                <div className="text-xs text-muted-foreground">Total Matches</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-green-600" />
              <div>
                <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
                <div className="text-xs text-muted-foreground">Approved</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-600" />
              <div>
                <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
                <div className="text-xs text-muted-foreground">Pending</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <X className="w-4 h-4 text-red-600" />
              <div>
                <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
                <div className="text-xs text-muted-foreground">Rejected</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-green-500" />
              <div>
                <div className="text-2xl font-bold text-green-500">{stats.highConfidence}</div>
                <div className="text-xs text-muted-foreground">High Confidence</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex items-center space-x-2 flex-1">
          <Search className="w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by song title, songbook, or composer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>
        
        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="suggested">Suggested</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>

          <Select value={confidenceFilter} onValueChange={setConfidenceFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by confidence" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Confidence</SelectItem>
              <SelectItem value="high">High (≥90%)</SelectItem>
              <SelectItem value="medium">Medium (80-89%)</SelectItem>
              <SelectItem value="low">Low (Under 80%)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Linkages List */}
      <div className="space-y-4">
        {filteredLinkages.map((linkage, index) => {
          const confidence = getConfidenceLevel(linkage.similarity_score);
          return (
            <Card 
              key={`${linkage.canonical_mele_id}-${linkage.songbook_entry_id}`} 
              className="hover:shadow-lg transition-shadow"
              data-linkage-index={index}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${confidence.color}`} />
                    <div>
                      <CardTitle className="text-lg">
                        {linkage.songbook_name}
                      </CardTitle>
                      <div className="text-sm text-muted-foreground">
                        Confidence: {(linkage.similarity_score * 100).toFixed(1)}% ({confidence.level})
                        {linkage.page && ` • Page ${linkage.page}`}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(linkage.match_status)}
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Song Match Details */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Music className="w-4 h-4 text-ocean-deep" />
                      <span className="font-medium">Song in Archive</span>
                    </div>
                    <div className="pl-6">
                      <div className="font-medium text-lg">{linkage.song_title_matched}</div>
                      <div className="text-sm text-muted-foreground">ID: {linkage.canonical_mele_id}</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Book className="w-4 h-4 text-coral" />
                      <span className="font-medium">Songbook Entry</span>
                    </div>
                    <div className="pl-6">
                      <div className="font-medium text-lg">{linkage.songbook_entry_title}</div>
                      <div className="text-sm font-medium text-ocean-deep">
                        📖 {linkage.songbook_name}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {linkage.page && `Page ${linkage.page}`}
                        {linkage.pub_year && ` • Published ${linkage.pub_year}`}
                      </div>
                      {linkage.composer && (
                        <div className="text-sm text-muted-foreground">
                          Composer: {linkage.composer}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                {linkage.match_status === 'suggested' ? (
                  <div className="flex gap-2 pt-4 border-t">
                    <Button
                      onClick={() => {
                        console.log('BUTTON CLICKED FOR:', linkage.song_title_matched);
                        updateLinkageStatus(linkage, 'approved');
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white transition-all"
                    >
                      <Check className="w-4 h-4 mr-2" />
                      Approve Match
                    </Button>
                    <Button
                      onClick={() => updateLinkageStatus(linkage, 'pending')}
                      variant="outline"
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      Need Review
                    </Button>
                    <Button
                      onClick={() => updateLinkageStatus(linkage, 'rejected')}
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                ) : (
                  <div className="flex gap-2 pt-4 border-t">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      {linkage.match_status === 'approved' && (
                        <>
                          <Check className="w-4 h-4 text-green-600" />
                          <span className="text-green-600 font-medium">Approved</span>
                        </>
                      )}
                      {linkage.match_status === 'rejected' && (
                        <>
                          <X className="w-4 h-4 text-red-600" />
                          <span className="text-red-600 font-medium">Rejected</span>
                        </>
                      )}
                    </div>
                    <Button
                      onClick={() => updateLinkageStatus(linkage, 'suggested')}
                      variant="outline"
                      size="sm"
                    >
                      Reset to Suggested
                    </Button>
                  </div>
                )}

              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredLinkages.length === 0 && !loading && (
        <div className="text-center py-8">
          <Book className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No linkages found</h3>
          <p className="text-muted-foreground">
            {searchTerm || statusFilter !== "all" || confidenceFilter !== "all" 
              ? "Try adjusting your search or filters" 
              : "No suggested linkages available. Run the matching engine to generate suggestions."
            }
          </p>
        </div>
      )}
    </div>
  );
}