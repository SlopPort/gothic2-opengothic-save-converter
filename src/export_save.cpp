#include <zenkit/SaveGame.hh>
#include <zenkit/World.hh>
#include <zenkit/vobs/Misc.hh>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <set>
#include <cmath>
#include <functional>
#include <limits>
using namespace zenkit;
std::ostream* out;
void s(const std::string& t) { *out << '"'; for(unsigned char c:t) { if(c=='"'||c=='\\') *out << '\\' << c; else if(c<32 || c>=128) *out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec; else *out << c; } *out << '"'; }
template<class T> void ints(const T& a) { *out << '['; bool sep=false; for(auto x:a) {if(sep)*out<<',';sep=true;*out<<x;} *out<<']'; }
void npc(const VNpc& n) {
 *out << "{\"instance\":";s(n.npc_instance);
 *out << ",\"player\":" << (n.player?"true":"false") << ",\"level\":"<<n.level<<",\"xp\":"<<n.xp<<",\"xpNext\":"<<n.xp_next_level<<",\"lp\":"<<n.lp<<",\"guild\":"<<n.guild<<",\"guildTrue\":"<<n.guild_true;
 *out << ",\"position\":["<<n.position.x<<','<<n.position.y<<','<<n.position.z<<"],\"rotation\":[";
 for(int i=0;i<3;i++){if(i)*out<<',';*out<<'['<<n.rotation[i][0]<<','<<n.rotation[i][1]<<','<<n.rotation[i][2]<<']';}*out<<']';
 *out << ",\"attributes\":";ints(n.attributes);*out<<",\"hitChance\":";ints(n.hit_chance);*out<<",\"aiVars\":";ints(n.aivar);
 *out << ",\"protection\":";ints(n.protection);*out<<",\"overlays\":[";for(size_t i=0;i<n.overlays.size();i++){if(i)*out<<',';s(n.overlays[i]);}*out<<']';
 *out << ",\"modelScale\":["<<n.model_scale.x<<','<<n.model_scale.y<<','<<n.model_scale.z<<"],\"modelFatness\":"<<n.model_fatness;
 *out << ",\"attitude\":"<<n.attitude<<",\"temporaryAttitude\":"<<n.attitude_temp;
 *out << ",\"missions\":";ints(n.missions);
 *out << ",\"fightTactic\":"<<n.fight_tactic<<",\"bodyStateOverride\":"<<n.bs_interruptable_override<<",\"npcType\":"<<n.npc_type;
 *out << ",\"flags\":"<<n.flags<<",\"routine\":";s(n.current_routine);
 *out << ",\"scriptWaypoint\":";s(n.script_waypoint);
 *out << ",\"ai\":{\"startState\":";s(n.start_ai_state);
 *out << ",\"currentValid\":"<<(n.current_state_valid?"true":"false")<<",\"currentName\":";s(n.current_state_name);
 *out << ",\"currentIndex\":"<<n.current_state_index<<",\"currentIsRoutine\":"<<(n.current_state_is_routine?"true":"false");
 *out << ",\"nextValid\":"<<(n.next_state_valid?"true":"false")<<",\"nextName\":";s(n.next_state_name);
 *out << ",\"nextIndex\":"<<n.next_state_index<<",\"nextIsRoutine\":"<<(n.next_state_is_routine?"true":"false")<<",\"lastState\":"<<n.last_ai_state;
 *out << ",\"hasRoutine\":"<<(n.has_routine?"true":"false")<<",\"respawn\":"<<(n.respawn?"true":"false")<<",\"respawnTime\":"<<n.respawn_time<<'}';
 *out << ",\"news\":[";bool news_sep=false;for(auto& news:n.news)if(news){if(news_sep)*out<<',';news_sep=true;
 *out << "{\"id\":"<<int(news->news_id)<<",\"told\":"<<(news->told?"true":"false")<<",\"spreadTime\":"<<news->spread_time<<",\"spreadType\":"<<int(news->spread_type)
       <<",\"gossip\":"<<(news->gossip?"true":"false")<<",\"guildVictim\":"<<(news->guild_victim?"true":"false")<<",\"witness\":";s(news->witness_name);
 *out<<",\"offender\":";s(news->offender_name);*out<<",\"victim\":";s(news->victim_name);*out<<'}';}*out<<']';
 *out << ",\"packed\":[";for(int i=0;i<9;i++){if(i)*out<<',';s(n.packed[i]);}*out<<']';
 *out << ",\"talents\":[";bool sep=false;for(auto& t:n.talents)if(t){if(sep)*out<<',';sep=true;*out<<'['<<t->talent<<','<<t->value<<','<<t->skill<<']';}*out<<']';
 *out << ",\"items\":[";sep=false; std::set<const VItem*> seen;
 auto item=[&](const std::shared_ptr<VItem>& i){if(!i || !seen.insert(i.get()).second)return;if(sep)*out<<',';sep=true;*out<<"{\"instance\":";s(i->instance);*out<<",\"amount\":"<<i->s_amount<<",\"flags\":"<<i->s_flags<<'}';};
 for(auto& i:n.items)item(i);for(auto& slot:n.slots)if(slot&&slot->used)item(slot->item);*out<<']';
 *out<<",\"spellHotkeys\":[";sep=false;
 for(size_t i=0;i<n.items.size();++i)if(n.items[i] && i<n.item_short_keys.size() && n.item_short_keys[i]>=0){
  if(sep)*out<<',';sep=true;*out<<'[';s(n.items[i]->instance);*out<<','<<n.item_short_keys[i]<<']';
 }*out<<']';
 *out<<",\"slots\":[";sep=false;for(auto& slot:n.slots)if(slot&&slot->used&&slot->item){if(sep)*out<<',';sep=true;*out<<'[';s(slot->name);*out<<',';s(slot->item->instance);*out<<']';}*out<<"]}";
}
int main(int argc,char** argv) { try {
 if(argc!=3)throw std::runtime_error("Usage: export_save save_directory output.json");
 SaveGame save(GameVersion::GOTHIC_2);save.load(argv[1]);std::ofstream f(argv[2]);out=&f;f<<std::setprecision(std::numeric_limits<float>::max_digits10);
 *out << "{\"format\":1,\"world\":";s(save.metadata.world);*out<<",\"date\":";s(save.metadata.save_date);*out<<",\"playSeconds\":"<<save.metadata.play_time_seconds<<",\"time\":["<<save.state.day<<','<<save.state.hour<<','<<save.state.minute<<"],\"symbols\":[";
 bool sep=false;for(auto& v:save.state.symbols){if(sep)*out<<',';sep=true;*out<<'[';s(v.name);*out<<',';ints(v.values);*out<<']';}*out<<"],\"infos\":[";
 sep=false;for(auto& v:save.state.infos){if(sep)*out<<',';sep=true;*out<<'[';s(v.name);*out<<','<<(v.told?"true":"false")<<']';}*out<<"],\"quests\":[";
 sep=false;for(auto& q:save.state.log){if(sep)*out<<',';sep=true;*out<<"{\"title\":";s(q.description);*out<<",\"section\":"<<int(q.section)<<",\"status\":"<<int(q.status)<<",\"entries\":[";bool es=false;for(auto& e:q.entries){if(es)*out<<',';es=true;s(e);}*out<<"]}";}*out<<"],\"worlds\":{";
 sep=false;for(auto& file:std::filesystem::directory_iterator(argv[1])) {auto name=file.path().stem().string();if(name!="NEWWORLD"&&name!="OLDWORLD"&&name!="ADDONWORLD"&&name!="DRAGONISLAND")continue;
 auto w=save.load_world(name);if(!w)continue;std::cerr<<name<<": "<<w->npcs.size()<<" NPCs, "<<w->world_vobs.size()<<" roots\n";if(sep)*out<<',';sep=true;s(name);*out<<":[";
 // Emit the complete NPC population, including the hero, without changing the source save.
 bool ns=false;std::set<const VNpc*> seenNpc;auto emit=[&](const std::shared_ptr<VNpc>& n){if(n&&seenNpc.insert(n.get()).second){if(ns)*out<<',';ns=true;npc(*n);}};
 std::function<void(const std::shared_ptr<VirtualObject>&)> visit=[&](const std::shared_ptr<VirtualObject>& v){if(!v)return;emit(std::dynamic_pointer_cast<VNpc>(v));for(auto& c:v->children)visit(c);};
 for(auto& v:w->world_vobs)visit(v);for(auto& n:w->npcs)emit(n);for(auto& sp:w->npc_spawns)emit(sp.npc);*out<<']';
 }*out<<"}}";f.flush();if(!f)throw std::runtime_error("Output write failed");
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;} }
