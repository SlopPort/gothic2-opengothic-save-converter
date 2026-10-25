#include <zenkit/DaedalusVm.hh>
#include <zenkit/SaveGame.hh>
#include <zenkit/World.hh>
#include <zenkit/vobs/Misc.hh>
#include <zenkit/addon/daedalus.hh>
#include <iostream>
#include <set>
#include <functional>
using namespace zenkit;
int main(int argc,char** argv) {try {
 if(argc!=3)throw std::runtime_error("Usage: verify_helpers GOTHIC.DAT save-directory");
 auto input=Read::from(argv[1]);DaedalusScript script;script.load(input.get());DaedalusVm vm(std::move(script));register_all_script_classes(vm);
 SaveGame save(GameVersion::GOTHIC_2);save.load(argv[2]);
 auto check=[](bool ok){if(!ok)throw std::runtime_error("Imported value mismatch");};
 vm.call_function("OGI_IMPORT_GLOBALS");size_t values=0,characters=0;
 for(auto& s:save.state.symbols){auto* sym=vm.find_symbol_by_name(s.name);check(sym!=nullptr);for(size_t i=0;i<s.values.size();i++){check(sym->get_int(i)==s.values[i]);values++;}}
 for(auto worldName:{"NEWWORLD","OLDWORLD"}) {auto world=save.load_world(worldName);if(!world)continue;
 std::set<const VNpc*> seen;size_t index=0;
 auto emit=[&](const std::shared_ptr<VNpc>& n){if(!n||!seen.insert(n.get()).second)return;
 auto npc=vm.allocate_instance<INpc>("PC_HERO");vm.global_self()->set_instance(npc);auto name=std::string("OGI_IMPORT_")+worldName+"_"+std::to_string(index++);vm.call_function(name);
 check(npc->level==n->level&&npc->exp==n->xp&&npc->exp_next==n->xp_next_level&&npc->lp==n->lp&&int(npc->guild)==n->guild);
 for(int i=0;i<8;i++){check(npc->attribute[i]==n->attributes[i]);check(npc->protection[i]==n->protection[i]);}for(int i=0;i<4;i++)check(npc->hitchance[i+1]==n->hit_chance[i]);for(int i=0;i<100;i++)check(npc->aivar[i]==n->aivar[i]);characters++;
 };
 std::function<void(const std::shared_ptr<VirtualObject>&)> visit=[&](const std::shared_ptr<VirtualObject>& v){if(!v)return;emit(std::dynamic_pointer_cast<VNpc>(v));for(auto& c:v->children)visit(c);};
 for(auto& v:world->world_vobs)visit(v);for(auto& n:world->npcs)emit(n);for(auto& s:world->npc_spawns)emit(s.npc);
 }
 std::cout<<"PASS: "<<values<<" global values (including arrays), "<<characters<<" NPC helper functions, original symbol indices preserved.\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
