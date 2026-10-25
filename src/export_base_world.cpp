#define main original_export_main
#include "export_save.cpp"
#undef main
#include <zenkit/vobs/MovableObject.hh>
#include <zenkit/vobs/Trigger.hh>
#include <zenkit/Vfs.hh>
int main(int argc,char** argv) { try {
 if(argc!=3)throw std::runtime_error("Usage: export_world save_directory output.json");
 Vfs vfs;vfs.mount_disk(std::filesystem::path(argv[1])/"Worlds.vdf");vfs.mount_disk(std::filesystem::path(argv[1])/"Worlds_Addon.vdf");std::ofstream f(argv[2]);out=&f;
 *out<<'{';bool ws=false;
 for(auto name:{"NEWWORLD","OLDWORLD"}) {
  auto node=vfs.find(std::string(name)+".ZEN");if(!node)continue;auto read=node->open_read();auto w=std::make_shared<World>();w->load(read.get(),GameVersion::GOTHIC_2);if(ws)*out<<',';ws=true;s(name);*out<<":[";
  bool sep=false;size_t count=0;
  std::set<const VirtualObject*> seen;
  std::function<void(const std::shared_ptr<VirtualObject>&,uint32_t)> visit=[&](const std::shared_ptr<VirtualObject>& v,uint32_t parent) {
   if(!v||!seen.insert(v.get()).second||std::dynamic_pointer_cast<VNpc>(v))return;
   if(sep)*out<<',';sep=true;++count;
   *out<<"{\"id\":"<<v->id<<",\"parent\":"<<parent<<",\"type\":"<<int(v->type)<<",\"name\":";s(v->vob_name);
   *out<<",\"visual\":";s(v->visual?v->visual->name:std::string());
   *out<<",\"show\":"<<(v->show_visual?"true":"false")<<",\"pos\":["<<v->position.x<<','<<v->position.y<<','<<v->position.z<<"],\"rot\":[";
   for(int i=0;i<3;i++){if(i)*out<<',';*out<<'[';for(int j=0;j<3;j++){if(j)*out<<',';*out<<v->rotation[i][j];}*out<<']';}*out<<']';
   if(std::dynamic_pointer_cast<VMover>(v))*out<<",\"mover\":true";
   *out<<'}';for(auto& c:v->children)visit(c,v->id);
  };
  for(auto& v:w->world_vobs)visit(v,uint32_t(-1));*out<<']';std::cerr<<name<<": "<<count<<" world objects\n";
 }
 *out<<'}';f.flush();if(!f)throw std::runtime_error("Write failed");
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
