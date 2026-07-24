/**
 * $api router
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/bom-entry',
      handler: 'bom-entry.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/bom-entry/:id',
      handler: 'bom-entry.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/bom-entry',
      handler: 'bom-entry.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/bom-entry/:id',
      handler: 'bom-entry.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/bom-entry/:id',
      handler: 'bom-entry.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
