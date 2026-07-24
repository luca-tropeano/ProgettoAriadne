export default {
  async bootstrap({ strapi }: { strapi: any }) {
    const eecCategories = [
      { categoryId: 1, name: "Cable Assemblies", subcategories: ["Data Transmission", "Fiber Optic", "RF-Microwave Assemblies"] },
      { categoryId: 2, name: "Capacitors", subcategories: ["Aluminum Solid", "Ceramic", "Film", "Glass", "Mica", "Semiconductor", "Tantalum"] },
      { categoryId: 3, name: "Diodes", subcategories: ["LED", "Rectifier", "Schottky", "TVS", "Zener"] },
      { categoryId: 4, name: "EMI/RFI Components", subcategories: ["Beads", "Ferrite Cores", "Filters"] },
      { categoryId: 5, name: "Fuses", subcategories: ["PTC Resettable", "Surface Mount", "Through Hole"] },
      { categoryId: 6, name: "Inductors", subcategories: ["Chokes", "Coils", "Transformers"] },
      { categoryId: 7, name: "Oscillators", subcategories: ["Crystals", "Oscillators", "Resonators"] },
      { categoryId: 8, name: "Optoelectronics", subcategories: ["Displays", "Phototransistors", "Sensors"] },
      { categoryId: 9, name: "Relays", subcategories: ["Reed", "Solid State"] },
      { categoryId: 10, name: "Resistors", subcategories: ["Film", "Metal Foil", "Network Arrays", "Potentiometers", "Thermistors", "Varistors"] },
      { categoryId: 11, name: "Switches", subcategories: ["DIP", "Pushbutton", "Slide", "Toggle"] },
      { categoryId: 12, name: "Transistors", subcategories: ["BJT", "Darlington", "FET", "MOSFET"] },
      { categoryId: 13, name: "Thyristors", subcategories: ["SCR", "Triac"] },
      { categoryId: 14, name: "Integrated Circuits", subcategories: ["Analog", "Digital", "Logic", "Memory", "Power Management", "RF"] },
      { categoryId: 15, name: "Connectors", subcategories: ["Board-to-Board", "Headers", "Terminal Blocks", "USB", "HDMI"] },
      { categoryId: 16, name: "Miscellaneous", subcategories: ["Battery Holders", "Heat Sinks", "Test Points"] },
    ];

    const existingCategories = await strapi.db.query("api::eec-category.eec-category").findMany({});
    if (existingCategories.length === 0) {
      for (const cat of eecCategories) {
        await strapi.entityService.create("api::eec-category.eec-category", { data: cat });
      }
    }

    const designators = [
      { designatorCode: "ANT", name: "Antenna", description: "Antenna", eecCategory: 16 },
      { designatorCode: "B", name: "Battery", description: "Batteria / pila", eecCategory: 16 },
      { designatorCode: "C", name: "Capacitor", description: "Condensatore", eecCategory: 2 },
      { designatorCode: "D", name: "Diode", description: "Diodo / LED", eecCategory: 3 },
      { designatorCode: "F", name: "Fuse", description: "Fusibile", eecCategory: 5 },
      { designatorCode: "H", name: "Hardware", description: "Componente meccanico (supporto, vite, distanziale)", eecCategory: 16 },
      { designatorCode: "J", name: "Jumper", description: "Jumper / connettore", eecCategory: 15 },
      { designatorCode: "K", name: "Relay", description: "Relè", eecCategory: 9 },
      { designatorCode: "L", name: "Inductor", description: "Induttore / induttanza", eecCategory: 6 },
      { designatorCode: "M", name: "Motor", description: "Motore", eecCategory: 16 },
      { designatorCode: "P", name: "Plug", description: "Connettore maschio / spina", eecCategory: 15 },
      { designatorCode: "Q", name: "Transistor", description: "Transistor / FET / MOSFET", eecCategory: 12 },
      { designatorCode: "R", name: "Resistor", description: "Resistore", eecCategory: 10 },
      { designatorCode: "S", name: "Switch", description: "Interruttore / switch / pulsante", eecCategory: 11 },
      { designatorCode: "T", name: "Transformer", description: "Trasformatore", eecCategory: 6 },
      { designatorCode: "U", name: "IC", description: "Circuito integrato / chip", eecCategory: 14 },
      { designatorCode: "X", name: "Socket", description: "Connettore femmina / socket", eecCategory: 15 },
      { designatorCode: "Y", name: "Crystal", description: "Cristallo / oscillatore", eecCategory: 7 },
      { designatorCode: "Z", name: "Unknown", description: "Componente non classificato / Zener", eecCategory: 16 },
    ];

    const existingDesignators = await strapi.db.query("api::reference-designator.reference-designator").findMany({});
    if (existingDesignators.length === 0) {
      for (const d of designators) {
        await strapi.entityService.create("api::reference-designator.reference-designator", { data: d });
      }
    }

    // Grant full CRUD to Public role on all collection types
    const publicRole = await strapi.db.query("plugin::users-permissions.role").findOne({ where: { type: "public" } });
    if (publicRole) {
      const apiTypes = [
        "api::eec-category.eec-category",
        "api::reference-designator.reference-designator",
        "api::device.device",
        "api::bom-entry.bom-entry",
        "api::component-material.component-material",
        "api::material.material",
        "api::audit-log.audit-log",
      ];
      const actions = ["find", "findOne", "create", "update", "delete"];

      for (const apiType of apiTypes) {
        for (const action of actions) {
          const existing = await strapi.db.query("plugin::users-permissions.permission").findOne({
            where: { action: `${apiType}.${action}`, role: publicRole.id },
          });
          if (!existing) {
            await strapi.db.query("plugin::users-permissions.permission").create({
              data: { action: `${apiType}.${action}`, role: publicRole.id },
            });
          }
        }
      }
      strapi.log.info("[bootstrap] Public role permissions configured for all API types");
    }
  },
};
