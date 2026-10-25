#define main original_export_main
#include "export_save.cpp"
#undef main
#include <zenkit/vobs/MovableObject.hh>
#include <zenkit/vobs/Trigger.hh>
int main(int argc,char** argv) { try {
 if(argc!=3)throw std::runtime_error("Usage: export_world save_directory output.json");
 SaveGame save(GameVersion::GOTHIC_2);save.load(argv[1]);std::ofstream f(argv[2]);out=&f;
 *out<<'{';bool ws=false;
 for(auto name:{"NEWWORLD","OLDWORLD"}) {
  auto w=save.load_world(name);if(!w)continue;if(ws)*out<<',';ws=true;s(name);*out<<":[";
  bool sep=false;size_t count=0;
  std::set<const VirtualObject*> seen;
  std::function<void(const std::shared_ptr<VirtualObject>&,uint32_t)> visit=[&](const std::shared_ptr<VirtualObject>& v,uint32_t parent) {
   if(!v||!seen.insert(v.get()).second||std::dynamic_pointer_cast<VNpc>(v))return;
   if(sep)*out<<',';sep=true;++count;
   *out<<"{\"id\":"<<v->id<<",\"parent\":"<<parent<<",\"type\":"<<int(v->type)<<",\"name\":";s(v->vob_name);
   *out<<",\"visual\":";s(v->visual?v->visual->name:std::string());
   *out<<",\"show\":"<<(v->show_visual?"true":"false")<<",\"pos\":["<<v->position.x<<','<<v->position.y<<','<<v->position.z<<"],\"rot\":[";
   for(int i=0;i<3;i++){if(i)*out<<',';*out<<'[';for(int j=0;j<3;j++){if(j)*out<<',';*out<<v->rotation[i][j];}*out<<']';}*out<<']';
   if(auto c=std::dynamic_pointer_cast<VContainer>(v)) {
    *out<<",\"container\":true,\"locked\":"<<(c->locked?"true":"false")<<",\"key\":";s(c->key);*out<<",\"pick\":";s(c->pick_string);
    *out<<",\"items\":[";bool is=false;for(auto& i:c->s_items)if(i){if(is)*out<<',';is=true;*out<<"{\"instance\":";s(i->instance);*out<<",\"amount\":"<<i->s_amount<<",\"flags\":"<<i->s_flags<<'}';}*out<<']';
   }
   if(auto d=std::dynamic_pointer_cast<VDoor>(v)){*out<<",\"door\":true,\"locked\":"<<(d->locked?"true":"false");}
   if(auto i=std::dynamic_pointer_cast<VItem>(v)){*out<<",\"item\":";s(i->instance);*out<<",\"amount\":"<<i->s_amount<<",\"flags\":"<<i->s_flags;}
   if(auto m=std::dynamic_pointer_cast<VMover>(v)){*out<<",\"mover\":true,\"frame\":"<<m->s_act_keyframe<<",\"nextFrame\":"<<m->s_next_keyframe<<",\"frameFloat\":"<<m->s_act_keyframe_f<<",\"direction\":"<<m->s_advance_dir<<",\"moverState\":"<<m->s_mover_state;}
   if(auto t=std::dynamic_pointer_cast<VTrigger>(v)){*out<<",\"trigger\":true,\"enabled\":"<<(t->s_is_enabled?"true":"false")<<",\"remaining\":"<<t->s_count_can_be_activated<<",\"maximum\":"<<t->max_activation_count<<",\"next\":"<<t->s_next_time_triggerable;}
   *out<<'}';for(auto& c:v->children)visit(c,v->id);
  };
  for(auto& v:w->world_vobs)visit(v,uint32_t(-1));*out<<']';std::cerr<<name<<": "<<count<<" world objects\n";
 }
 *out<<'}';f.flush();if(!f)throw std::runtime_error("Write failed");
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
