// Synthetic original-save records; no game assets or save fixtures are required.
#include <zenkit/Archive.hh>
#include <zenkit/vobs/Misc.hh>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace zenkit;

void check(bool condition,const char* message) {
  if(!condition)throw std::runtime_error(message);
}

int main() {try {
  for(auto format : {ArchiveFormat::BINARY,ArchiveFormat::BINSAFE}) {
    auto source=std::make_shared<VNpc>();
    source->npc_instance="SYNTHETIC_NPC";
    for(size_t i=0;i<VNpc::packed_count;++i)source->packed[i]="ITEM_"+std::to_string(i)+":1";
    for(int key : {3,10,0}) {
      auto item=std::make_shared<VItem>();item->instance="SYNTHETIC_RUNE";
      item->s_amount=1;item->s_flags=0x200;
      source->items.push_back(item);source->item_short_keys.push_back(key);
    }
    std::vector<std::byte> bytes;
    auto output=Write::to(&bytes);
    auto writer=WriteArchive::to_save(output.get(),format);
    writer->write_object(source,GameVersion::GOTHIC_2);
    writer->write_header();writer.reset();
    auto input=Read::from(&bytes);auto reader=ReadArchive::from(input.get());
    auto restored=reader->read_object<VNpc>(GameVersion::GOTHIC_2);
    check(bool(restored),"NPC record did not round-trip");
    check(restored->items.size()==3,"Inventory item count changed");
    check(restored->item_short_keys==source->item_short_keys,"Spell hotkeys were not preserved");
    for(size_t i=0;i<VNpc::packed_count;++i)check(restored->packed[i]==source->packed[i],"Packed inventory category changed");
  }
  std::cout<<"Synthetic NPC inventory and spell-hotkey round trips passed\n";
 }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}}
