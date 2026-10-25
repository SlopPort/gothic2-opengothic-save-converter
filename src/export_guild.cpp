#include <zenkit/SaveGame.hh>
#include <fstream>
int main(int argc,char**argv){if(argc!=3)return 2;zenkit::SaveGame s(zenkit::GameVersion::GOTHIC_2);s.load(argv[1]);std::ofstream o(argv[2],std::ios::binary);o.write((const char*)s.state.guild_attitudes,42*42);}
