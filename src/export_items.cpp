#include <zenkit/DaedalusVm.hh>
#include <zenkit/addon/daedalus.hh>
#include <fstream>
#include <filesystem>
#include <stdexcept>
#include <iostream>
using namespace zenkit;
std::ofstream out;
void put(const std::string& s){uint32_t n=s.size();out.write((char*)&n,4);out.write(s.data(),n);}
template<class T> void put(const T& v){static_assert(sizeof(T)==4);out.write((const char*)&v,4);}
template<class T,size_t N> void put(const T(&v)[N]){for(auto& x:v)put(x);}
template<class... T> void fields(const T&... v){(put(v),...);}
int main(int argc,char** argv){try{
 if(argc<4)throw std::runtime_error("Usage: export_items GOTHIC.DAT output_directory INSTANCE [...]");
 std::filesystem::create_directories(argv[2]);
 auto input=Read::from(argv[1]);DaedalusScript script;script.load(input.get());DaedalusVm vm(std::move(script));register_all_script_classes(vm);
 for(int arg=3;arg<argc;arg++){
 const char* name=argv[arg];
 if(std::string(name).find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")!=std::string::npos)throw std::runtime_error("Invalid item instance name");
 auto p=vm.init_instance<IItem>(name);auto& h=*p;out.open(std::string(argv[2])+"/"+name+".item",std::ios::binary);
 fields(uint32_t(h.symbol_index()),h.id,h.name,h.name_id,h.hp,h.hp_max,h.main_flag);
 fields(h.flags,h.weight,h.value,h.damage_type,h.damage_total,h.damage,h.wear,h.protection,h.nutrition,h.cond_atr,h.cond_value,h.change_atr,h.change_value,h.magic,h.on_equip,h.on_unequip,h.on_state,h.owner,h.owner_guild,h.disguise_guild,h.visual,h.visual_change,h.effect,h.visual_skin,h.scheme_name,h.material,h.munition,h.spell,h.range,h.mag_circle,h.description,h.text,h.count,h.inv_zbias,h.inv_rot_x,h.inv_rot_y,h.inv_rot_z,h.inv_animate);
 put(uint32_t(1));fields(0.f,0.f,0.f);out.put(0);out.put(char(255));for(int i=0;i<16;i++)put(i%5==0?1.f:0.f);out.close();std::cout<<name<<" exported\n";
 }
 }catch(const std::exception& e){std::cerr<<e.what();return 1;}}
